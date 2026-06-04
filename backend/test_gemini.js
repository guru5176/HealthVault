import { GoogleGenAI } from '@google/genai';
import dotenv from 'dotenv';
dotenv.config();

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

async function test() {
  const models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash'];
  for (const model of models) {
    try {
      console.log(`Testing model: ${model}...`);
      const response = await ai.models.generateContent({
        model: model,
        contents: 'Hello',
      });
      console.log(`Success with ${model}! Response:`, response.text);
      return;
    } catch (e) {
      console.error(`Failed with ${model}:`, e.message);
    }
  }
}

test();
