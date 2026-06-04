import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import multer from 'multer';
import { GoogleGenAI } from '@google/genai';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { execFile } from 'child_process';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

const upload = multer({ storage: multer.memoryStorage() });

// Initialize Gemini API
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// In-memory store for the most recently uploaded document text/context
let currentDocumentContext = "";

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'HealthVault API is running' });
});

app.post('/api/upload', upload.single('document'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No document image provided' });
    }
    
    console.log(`Received file: ${req.file.originalname}, size: ${req.file.size} bytes`);
    
    const prompt = `
      You are a specialized medical document extraction AI.
      Analyze this image of a medical document (which could be a prescription, test result, or doctor's note).
      Extract the following information and output ONLY a valid JSON object matching this structure:
      {
        "recordType": "e.g., Prescription, Blood Test, Consultation Note",
        "date": "Date found on document, or current ISO date if not found",
        "findings": "A concise summary of the key findings, conditions, or prescribed medications",
        "doctor": "Name of the prescribing or signing doctor",
        "rawText": "The full transcription of all key text on the document."
      }
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: [
        {
          role: 'user',
          parts: [
            {
              inlineData: {
                data: req.file.buffer.toString("base64"),
                mimeType: req.file.mimetype
              }
            },
            {
              text: prompt
            }
          ]
        }
      ],
      config: {
        responseMimeType: "application/json",
      }
    });

    const parsedData = JSON.parse(response.text);
    
    // Save to context for RAG query
    currentDocumentContext = `
      Document Type: ${parsedData.recordType}
      Date: ${parsedData.date}
      Doctor: ${parsedData.doctor}
      Findings SUMMARY: ${parsedData.findings}
      Full Document Text: ${parsedData.rawText}
    `;

    res.json({
      message: 'Document analyzed successfully',
      data: {
        recordType: parsedData.recordType || "Medical Record",
        date: parsedData.date || new Date().toISOString(),
        findings: parsedData.findings || "No specific findings extracted.",
        doctor: parsedData.doctor || "Unknown Provider"
      }
    });
  } catch (error) {
    console.error('Error in /api/upload:', error);
    res.status(500).json({ error: 'Failed to process document using Gemini API.' });
  }
});

app.post('/api/query', async (req, res) => {
  try {
    const { query } = req.body;
    if (!query) {
      return res.status(400).json({ error: 'No query provided' });
    }
    
    let systemPrompt = `
      You are the HealthVault AI Assistant.
      You are a helpful and knowledgeable medical AI. 
      Answer the user's questions based on the uploaded document context if available.
      If the question is a general medical question, answer it helpfully using your internal knowledge.
      If the user asks about something specific to them that is not in the document context, politely inform them you can't find that in their records.
      Keep answers concise and conversational but professional.
      
      CURRENT UPLOADED DOCUMENT CONTEXT (Use this to answer queries about the user's records):
      ${currentDocumentContext ? currentDocumentContext : "No documents currently uploaded."}
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: query,
      config: {
        systemInstruction: systemPrompt
      }
    });

    res.json({
      query,
      answer: response.text,
      sources: currentDocumentContext ? ["Recently Scanned Medical Document"] : []
    });
  } catch (error) {
    console.error('Error in /api/query:', error);
    res.status(500).json({ error: 'Failed to process query using Gemini API.' });
  }
});

app.post('/api/predict-drug', upload.single('document'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No image provided' });

    const tempPath = path.join(os.tmpdir(), `upload_${Date.now()}.jpg`);
    fs.writeFileSync(tempPath, req.file.buffer);

    // Predict using python script
    const scriptPath = path.resolve('../ml/predict_api.py');
    execFile('python', [scriptPath, tempPath], (error, stdout, stderr) => {
      // Clean up temp file
      try { fs.unlinkSync(tempPath); } catch (e) {}

      if (error) {
        console.error('Python execution error:', error);
        console.error('stderr:', stderr);
        return res.status(500).json({ error: 'Failed to run OCR model locally' });
      }

      try {
        const result = JSON.parse(stdout);
        if (result.error) return res.status(500).json(result);
        res.json({ prediction: result.prediction });
      } catch (parseErr) {
        console.error('Parse error:', parseErr);
        console.log('Raw output:', stdout);
        res.status(500).json({ error: 'Invalid response from model' });
      }
    });
  } catch (err) {
    console.error('Error in /api/predict-drug:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
