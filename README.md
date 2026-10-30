<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-000000?logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/MLflow-2.16-0194E2?logo=mlflow&logoColor=white" alt="MLflow">
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white" alt="MongoDB">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/GPU-RTX_4060-76B900?logo=nvidia&logoColor=white" alt="NVIDIA RTX 4060">
</p>

<h1 align="center">🏥 Health Wallet</h1>

<p align="center">
  <strong>Privacy-First Medical Records Management with On-Device AI Inference & Production MLOps</strong>
</p>

<p align="center">
  A full-stack healthcare application that combines AI-powered prescription scanning, a context-aware health assistant, and privacy-preserving specialist routing — all running <strong>100% locally</strong> on your hardware. No patient data ever leaves the device.
</p>

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [API Reference](#-api-reference)
- [MLOps Pipeline](#-mlops-pipeline)
- [Frontend](#-frontend)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Team](#-team)

---

## ✨ Key Features

### 🗄️ Health Vault — Secure Medical Records
- **Prescription Scanner**: Upload handwritten prescription images → TrOCR extracts text → local LLM structures it into clean Markdown records
- **Full-Text Search**: Instantly search across all medical records with keyword matching and contextual line highlights
- **Dual Storage**: Records stored locally as Markdown files + persisted to MongoDB Atlas for cloud backup
- **Categorization**: Automatic classification into medications, timeline, and general categories

### 💬 AI Health Assistant — RAG-Powered Chat
- **Retrieval-Augmented Generation**: The assistant retrieves only the most relevant health records using keyword scoring before answering
- **Streaming Responses**: Real-time token-by-token output via Server-Sent Events (SSE) for an interactive chat experience
- **Conversation Memory**: Maintains a sliding window of the last 5 conversation turns for contextual follow-up questions
- **Grounded Answers**: Strictly answers from your records — never fabricates medical information

### 🩺 Care Router — Privacy-Preserving Specialist Routing
- **PII Anonymization**: Local LLM strips all personally identifiable information (names, SSNs, DOBs, phone numbers) before any analysis
- **Specialty Detection**: AI determines the correct medical specialty (cardiology, psychiatry, endocrinology, etc.) from clinical intent
- **Provider Search**: Queries MongoDB for matching specialists, filtered by location and availability
- **Drug Interaction Checker**: Checks pairwise interactions across a curated database of common medications with severity ratings

### 📊 MLOps & Monitoring
- **MLflow Experiment Tracking**: Every inference is logged with model name, prompt version, latency, token throughput, and full prompt/response artifacts
- **Real-Time Inference Monitor**: Rolling-window metrics with P50/P95/P99 latencies, tokens/sec, error rates, and per-model breakdowns
- **Runtime Model Switching**: Hot-swap between Ollama models (e.g., `deepseek-r1:7b` → `gemma3:4b`) without restarting the server
- **Health Checks**: Comprehensive `/api/health` endpoint reporting Ollama, MongoDB, and GPU status

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Frontend["Frontend SPA"]
        UI["HTML5 / CSS3 / Vanilla JS"]
        Dash["Dashboard View"]
        VaultUI["Vault UI + Prescription Scanner"]
        ChatUI["AI Chat (SSE Streaming)"]
        CareUI["Care Router + Privacy Bridge"]
    end

    subgraph Backend["FastAPI Backend"]
        API["API Router Layer"]
        VaultSvc["Vault Service"]
        ChatSvc["Chat Service (RAG)"]
        CareSvc["Care Router Service"]
        OCRSvc["OCR Service (TrOCR)"]
        DrugSvc["Drug Interaction Checker"]
    end

    subgraph ML["Machine Learning Layer"]
        ModelSvr["Model Server (Ollama Client)"]
        Prompts["Versioned Prompt System"]
        Monitor["Inference Monitor"]
        Registry["MLflow Registry"]
    end

    subgraph Data["Data & Storage"]
        Mongo[("MongoDB Atlas")]
        LocalFS[("Local Markdown Files")]
        MLflowDB[("MLflow Tracking Store")]
    end

    subgraph GPU["Local GPU Inference"]
        Ollama["Ollama — DeepSeek R1 7B"]
        TrOCR["TrOCR — Handwritten OCR"]
    end

    UI --> API
    API --> VaultSvc & ChatSvc & CareSvc

    VaultSvc --> OCRSvc
    VaultSvc --> Mongo & LocalFS
    OCRSvc --> TrOCR

    ChatSvc --> ModelSvr
    CareSvc --> ModelSvr & DrugSvc

    ModelSvr --> Ollama
    ModelSvr --> Monitor --> Registry --> MLflowDB
```

### Data Flow — Prescription Upload Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  User drops  │───▶│   TrOCR     │───▶│  Local LLM  │───▶│   Vault     │───▶│   MongoDB    │
│  image file  │    │  extracts   │    │  structures  │    │  saves .md  │    │  persists    │
│  (PNG/JPG)   │    │  raw text   │    │  Markdown    │    │  locally    │    │  to cloud    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
```

### Data Flow — Care Router Privacy Bridge

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Patient Data │───▶│  PII Strip   │───▶│  Specialty   │───▶│  Provider    │───▶│  Action Plan │
│  (with PII)   │    │  (Local LLM) │    │  Detection   │    │  Search      │    │  (No PII)    │
│  Names, SSN,  │    │  Anonymized  │    │  AI Routing  │    │  MongoDB     │    │  Safe Output │
│  DOB, etc.    │    │  on-device   │    │              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11, FastAPI 0.115, Uvicorn | Async web framework with OpenAPI docs |
| **LLM Inference** | Ollama, DeepSeek R1 7B | Local large language model serving |
| **OCR** | Microsoft TrOCR (base-handwritten) | Handwritten prescription text extraction |
| **Deep Learning** | PyTorch ≥ 2.3, Transformers ≥ 4.40 | Model runtime and tokenization |
| **Database** | MongoDB Atlas, PyMongo 4.8 | Persistent cloud storage with local fallback |
| **Experiment Tracking** | MLflow 2.16 | Inference logging, prompt versioning, metrics |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | SPA with SSE streaming, drag-and-drop UI |
| **Containerization** | Docker, Docker Compose | Multi-service orchestration with GPU passthrough |
| **GPU** | NVIDIA RTX 4060 (8 GB VRAM) | fp16 inference for both LLM and OCR |
| **Monitoring** | Custom InferenceMonitor | Real-time P50/P95/P99 latencies, throughput |

---

## 📁 Project Structure

```
health-wallet/
├── backend/
│   ├── api/                        # FastAPI route handlers
│   │   ├── routes_vault.py         #   Vault CRUD + prescription upload
│   │   ├── routes_chat.py          #   AI chat (SSE streaming + non-streaming)
│   │   ├── routes_care.py          #   Care router + drug interaction checker
│   │   └── routes_health.py        #   Health checks, metrics, model management
│   ├── services/                   # Business logic layer
│   │   ├── vault_service.py        #   Record management + MongoDB persistence
│   │   ├── chat_service.py         #   RAG chat with keyword-scored retrieval
│   │   ├── care_router.py          #   PII anonymization + specialist routing
│   │   ├── drug_checker.py         #   Drug-drug interaction database
│   │   └── ocr_service.py          #   TrOCR handwritten text extraction
│   ├── ml/                         # Machine learning & MLOps
│   │   ├── model_server.py         #   Ollama API client (generate, chat, stream)
│   │   ├── model_registry.py       #   MLflow experiment logging
│   │   ├── monitor.py              #   Real-time inference metrics (P50/P95/P99)
│   │   └── prompts.py              #   Versioned system prompts (v1.0.0)
│   ├── db/                         # Database layer
│   │   ├── mongo.py                #   MongoDB Atlas connection + collections
│   │   └── seed.py                 #   Database seeding utilities
│   ├── data/health_vault/          #   Local Markdown record storage
│   ├── config.py                   #   Pydantic settings (env-driven config)
│   └── main.py                     #   FastAPI app entry point + lifecycle
├── frontend/
│   ├── index.html                  # SPA shell with all views
│   ├── css/styles.css              # Responsive dashboard styling
│   └── js/app.js                   # Client-side logic + SSE chat
├── docs/
│   ├── architecture.md             # System architecture documentation
│   ├── api_reference.md            # API endpoint reference
│   └── mlops_strategies.md         # MLOps implementation guide
├── tests/
│   └── conftest.py                 # Pytest fixtures and test configuration
├── mlflow_data/                    # MLflow tracking store (local)
├── docker-compose.yml              # Multi-service orchestration
├── Dockerfile                      # Application container image
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # ← You are here
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.11+ | Required for all backend services |
| **Ollama** | Latest | Local LLM serving engine |
| **MongoDB** | Atlas or local | Optional — app works without it using fallbacks |
| **NVIDIA GPU** | RTX 4060+ recommended | Optional — CPU fallback available |
| **Docker** | 20.10+ | Only if using containerized deployment |
| **NVIDIA Container Toolkit** | Latest | Only if using Docker with GPU |

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/SECE-24-28/healthwallet-ta-mlops-project.git
cd healthwallet-ta-mlops-project
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Install and start Ollama**

```bash
# Install Ollama from https://ollama.com
# Then pull the default model:
ollama pull deepseek-r1:7b

# Start the Ollama server:
ollama serve
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b

# MongoDB (optional — leave empty to use local fallback)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DB=health_wallet

# MLflow
MLFLOW_TRACKING_URI=./mlflow_data

# Application
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Running Locally

```bash
# Start the application
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at **http://localhost:8000** to access the Health Wallet dashboard.

### Running with Docker

```bash
# Build and start all services (app + Ollama with GPU)
docker-compose up --build

# Run in detached mode
docker-compose up --build -d
```

> **Note**: The Docker Compose configuration includes NVIDIA GPU passthrough for accelerated inference. Ensure the NVIDIA Container Toolkit is installed on the host.

---

## 📡 API Reference

All endpoints are served at `http://localhost:8000`. Interactive API docs are available at `/docs` (Swagger UI) and `/redoc`.

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check (Ollama + MongoDB status) |
| `GET` | `/api/health/metrics` | Real-time inference metrics (P50/P95/P99 latency, throughput) |
| `GET` | `/api/health/models` | List available Ollama models |
| `POST` | `/api/health/switch-model` | Hot-swap the active LLM model at runtime |
| `GET` | `/api/health/model-stats` | Per-model inference statistics |
| `GET` | `/api/health/experiments` | Recent MLflow experiment runs |

### Vault (Medical Records)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/vault/records` | List all health records (filterable by `?category=`) |
| `GET` | `/api/vault/records/{id}` | Get a single record by ID |
| `POST` | `/api/vault/records` | Create a new health record |
| `POST` | `/api/vault/upload-prescription` | Upload prescription image → OCR → LLM → structured record |
| `GET` | `/api/vault/search?q=` | Full-text search across all records |

### AI Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a message (streaming via SSE or full response) |
| `GET` | `/api/chat/history` | Get conversation history |
| `POST` | `/api/chat/clear` | Clear conversation history |

### Care Router

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/care/anonymize` | Strip PII from patient data using local LLM |
| `POST` | `/api/care/route` | Route patient to appropriate specialist |
| `POST` | `/api/care/drug-check` | Check drug-drug interactions for a medication list |

### Example Requests

<details>
<summary><strong>Upload a Prescription</strong></summary>

```bash
curl -X POST http://localhost:8000/api/vault/upload-prescription \
  -F "file=@prescription.jpg"
```

**Response:**
```json
{
  "message": "Prescription processed successfully",
  "ocr_raw": "Amoxicillin 500mg three times daily...",
  "structured": "# Prescription Record\n\n## Prescribed Medications\n- **Amoxicillin** 500mg - 3x daily - 7 days\n  * Instructions: Take with food\n\n## Safety & Clinical Notes\n- Note: Transcribed locally using OCR...",
  "record": { "id": "Prescription_-_Amoxicillin", "title": "Prescription - Amoxicillin", ... },
  "mongo_saved": true
}
```
</details>

<details>
<summary><strong>Chat with AI Assistant</strong></summary>

```bash
# Streaming (SSE)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What medications am I currently taking?", "stream": true}'

# Non-streaming
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What medications am I currently taking?", "stream": false}'
```
</details>

<details>
<summary><strong>Route Patient to Specialist</strong></summary>

```bash
curl -X POST http://localhost:8000/api/care/route \
  -H "Content-Type: application/json" \
  -d '{"clinical_intent": "Patient on escitalopram 10mg for anxiety, A1C 6.8%", "city": "San Francisco"}'
```

**Response:**
```json
{
  "specialty": "psychiatry",
  "reasoning": "Patient on SSRI for anxiety management...",
  "providers": [
    { "name": "Dr. Maria Reyes", "specialty": "Psychiatry", "hospital": "St. Luke's Medical Center", "rating": 4.7 }
  ],
  "drug_interactions": [],
  "privacy_note": "All PII was stripped on-device before this analysis."
}
```
</details>

<details>
<summary><strong>Check Drug Interactions</strong></summary>

```bash
curl -X POST http://localhost:8000/api/care/drug-check \
  -H "Content-Type: application/json" \
  -d '{"medications": ["escitalopram", "tramadol", "ibuprofen"]}'
```

**Response:**
```json
{
  "medications": ["escitalopram", "tramadol", "ibuprofen"],
  "interactions": [
    {
      "drug_a": "escitalopram", "drug_b": "tramadol",
      "severity": "high",
      "description": "Increased risk of serotonin syndrome and seizures.",
      "recommendation": "Avoid combination. Monitor closely."
    },
    {
      "drug_a": "escitalopram", "drug_b": "ibuprofen",
      "severity": "moderate",
      "description": "SSRIs may increase bleeding risk with NSAIDs.",
      "recommendation": "Use with caution."
    }
  ],
  "interaction_count": 2,
  "has_critical": false
}
```
</details>

---

## 📊 MLOps Pipeline

Health Wallet implements a production-grade MLOps pipeline designed for privacy-preserving, on-device AI:

### 1. Local Model Serving

All inference runs entirely on-device via Ollama. No API keys, no cloud calls, no data leakage.

```
User Query → FastAPI → Model Server → Ollama (GPU) → Response
                                ↓
                         Inference Monitor
                                ↓
                          MLflow Logging
```

### 2. Experiment Tracking (MLflow)

Every inference call is automatically logged:

| What's Tracked | Details |
|---------------|---------|
| **Parameters** | Model name, prompt version, endpoint, success/failure |
| **Metrics** | Latency (ms), token count, tokens/sec throughput |
| **Artifacts** | Full prompt text and LLM response (truncated to 2 KB) |

### 3. Real-Time Monitoring

The `InferenceMonitor` maintains a rolling window of the last 1,000 inference events:

- **Latency Percentiles**: P50, P95, P99 for identifying long-tail issues
- **Throughput**: Average tokens/sec and requests/min (5-minute window)
- **Error Rates**: Real-time failure tracking with per-model breakdowns
- **API Endpoint**: `/api/health/metrics` — ready for Grafana or Prometheus integration

### 4. Prompt Versioning

All system prompts are centrally managed in `backend/ml/prompts.py` with semantic versioning (`v1.0.0`). Every MLflow run logs the prompt version, enabling A/B testing across prompt iterations.

### 5. Runtime Model Switching

Hot-swap models via the API without server restart:

```bash
curl -X POST http://localhost:8000/api/health/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma3:4b"}'
```

---

## 🖥️ Frontend

The frontend is a responsive Single Page Application (SPA) built with vanilla HTML5, CSS3, and JavaScript — no build step required.

### Views

| View | Description |
|------|-------------|
| **📊 Dashboard** | At-a-glance stats (record count, prescriptions, consultations, referrals) with quick-action buttons |
| **🗄️ My Records** | Browse, search, and filter medical records. Drag-and-drop prescription scanner with live processing status |
| **💬 AI Assistant** | Real-time chat with streaming responses. Model selector for switching between available LLMs |
| **🩺 Care Router** | Interactive privacy bridge demo showing PII stripping, specialty detection, provider search, and drug interaction checking |

### Key Frontend Features
- **Server-Sent Events (SSE)** for real-time streaming chat
- **Drag-and-Drop** prescription image upload
- **Live System Status** indicators for Ollama, MongoDB, and GPU in the sidebar
- **Responsive Design** with mobile navigation toggle
- **Markdown Rendering** for medical records display

---

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 👥 Team

**SECE-24-28** — Guru Aravinth S || Dineshkumar S

---

<p align="center">
  Built with ❤️ using <strong>FastAPI</strong>, <strong>Ollama</strong>, <strong>TrOCR</strong>, and <strong>MLflow</strong>
  <br>
  <em>Privacy-first. On-device. Always.</em>
</p>
