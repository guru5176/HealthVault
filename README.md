# HealthVault

AI-powered medical document processing and health record management system.

## Overview

HealthVault allows users to upload medical documents (prescriptions, test results, consultation notes) and uses AI to extract structured data. Users can also chat with their health records using a RAG-powered conversational interface.

## Architecture

```
HealthVault/
├── frontend/          # React + TypeScript + Vite
│   └── src/
│       ├── App.tsx              # Main application with chat & scan UI
│       ├── components/          # Reusable components
│       └── index.css            # Glassmorphic design system
├── backend/           # Express.js API server
│   └── server.js               # Gemini API integration
└── README.md
```

## AI Integration

| Phase | Model | Mode | Status |
|-------|-------|------|--------|
| Phase 1 | **Gemini 2.5 Flash** | Cloud API | ✅ Active |
| Phase 2 | **LLaMA** | Offline / On-device | 🔜 Planned |

## Features

- 📄 **Document Scanning** — Upload medical documents for AI-powered data extraction
- 🧠 **Structured Extraction** — Automatically identifies record type, date, doctor, and findings
- 💬 **RAG Chat** — Ask questions about your health records in natural language
- 🌙 **Dark/Light Theme** — Glassmorphic UI with theme toggle
- 🔒 **Privacy-First** — Future offline mode with LLaMA for fully on-device processing

## Getting Started

### Prerequisites
- Node.js 18+
- Gemini API Key

### Backend
```bash
cd backend
npm install
echo "GEMINI_API_KEY=your_key_here" > .env
node server.js
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## License

Private — All rights reserved.
