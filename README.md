# 🏥 Health Wallet — Privacy-First Medical Records + AI Specialist Routing

> **An MLOps-powered healthcare application that keeps all patient data on-device.** No PII ever leaves your machine — local LLM inference via Ollama on NVIDIA RTX 4060.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-white.svg)](https://ollama.com/)
[![MLflow](https://img.shields.io/badge/MLflow-2.16-0194E2.svg)](https://mlflow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [MLOps Pipeline](#mlops-pipeline)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Team](#team)

---

## Overview

Health Wallet is a **privacy-first medical records management system** that combines:

- **Health Passport (Vault)** — Securely store and manage medical records, prescriptions, and health data locally
- **Soma Care Router** — AI-powered specialist routing that anonymizes patient data before analysis
- **AI Chat Assistant** — Medical Q&A powered by local LLM inference (no cloud APIs)
- **Prescription OCR** — Extract text from medical prescriptions using PaddleOCR

All AI inference runs **locally on your GPU** via Ollama — zero patient data is sent to external servers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/CSS/JS)                │
│              SPA served by FastAPI StaticFiles           │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────────┐  │
│  │  Vault   │ │   Chat   │ │  Care  │ │   Health    │  │
│  │  Routes  │ │  Routes  │ │ Routes │ │   Routes    │  │
│  └────┬─────┘ └────┬─────┘ └───┬────┘ └──────┬──────┘  │
│       │             │           │              │         │
│  ┌────▼─────────────▼───────────▼──────────────▼──────┐ │
│  │              Service Layer                         │ │
│  │  vault_service │ chat_service │ care_router │ OCR  │ │
│  └────────────────┬───────────────────────────────────┘ │
│                   │                                     │
│  ┌────────────────▼───────────────────────────────────┐ │
│  │              ML Layer                              │ │
│  │  model_server │ monitor │ model_registry │ prompts │ │
│  └────────────────┬───────────────────────────────────┘ │
└───────────────────┼─────────────────────────────────────┘
                    │
        ┌───────────▼───────────┐       ┌──────────────┐
        │   Ollama (Local LLM)  │       │  MongoDB     │
        │   deepseek-r1:7b      │       │  Atlas       │
        │   RTX 4060 (8GB VRAM) │       │              │
        └───────────────────────┘       └──────────────┘
                                        ┌──────────────┐
                                        │   MLflow     │
                                        │  (Local)     │
                                        └──────────────┘
```

---

## Features

### 🔐 Health Vault (Medical Records)
- Upload and store medical records securely
- Prescription image upload with OCR text extraction (PaddleOCR)
- Record categorization and search
- All data stored locally or in your own MongoDB Atlas instance

### 🤖 AI Chat Assistant
- Medical Q&A powered by local LLM (deepseek-r1:7b via Ollama)
- Real-time streaming responses via Server-Sent Events (SSE)
- Context-aware conversations with chat history
- No data sent to external APIs

### 🏥 Soma Care Router
- AI-powered specialist routing based on clinical intent
- **Privacy bridge** — PII is stripped on-device before any analysis
- Provider search with MongoDB backend (with fallback data)
- Drug interaction checking for mentioned medications

### 📊 MLOps Monitoring
- Real-time inference metrics (latency, throughput, error rates)
- MLflow experiment tracking for all inference runs
- Per-model performance statistics (P50, P95, P99 latencies)
- GPU utilization tracking for RTX 4060

### 🔍 Prescription OCR
- Extract text from prescription images using PaddleOCR
- Supports multiple image formats
- Automatic text region detection and recognition

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.115, Uvicorn, Python 3.11 |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (SPA) |
| **LLM Inference** | Ollama (deepseek-r1:7b), NVIDIA RTX 4060 |
| **Database** | MongoDB Atlas (optional, has fallback) |
| **OCR** | PaddleOCR |
| **Experiment Tracking** | MLflow 2.16 |
| **Monitoring** | Custom inference monitor (latency/throughput/errors) |
| **Containerization** | Docker, Docker Compose |
| **Logging** | structlog + Python logging |

---

## Project Structure

```
health-wallet/
├── backend/
│   ├── main.py                 # FastAPI app entry point & lifespan
│   ├── config.py               # Pydantic settings from .env
│   ├── api/
│   │   ├── routes_vault.py     # Medical records CRUD endpoints
│   │   ├── routes_chat.py      # AI chat with streaming (SSE)
│   │   ├── routes_care.py      # Specialist routing endpoints
│   │   └── routes_health.py    # Health check & monitoring endpoints
│   ├── services/
│   │   ├── vault_service.py    # Medical records business logic
│   │   ├── chat_service.py     # Chat session management
│   │   ├── care_router.py      # Privacy-preserving specialist routing
│   │   ├── drug_checker.py     # Drug interaction checking
│   │   └── ocr_service.py      # PaddleOCR prescription extraction
│   ├── ml/
│   │   ├── model_server.py     # Ollama client (generate, chat, stream)
│   │   ├── monitor.py          # Inference metrics (rolling window)
│   │   ├── model_registry.py   # MLflow experiment logging
│   │   └── prompts.py          # System prompts & prompt versioning
│   ├── db/
│   │   ├── mongo.py            # MongoDB Atlas connection
│   │   └── seed.py             # Database seeding scripts
│   └── data/                   # Local data storage
├── frontend/
│   ├── index.html              # Single-page application
│   ├── css/
│   │   └── styles.css          # Application styles
│   └── js/                     # Frontend JavaScript
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_api.py             # API endpoint tests
│   └── test_model.py           # ML model tests
├── Dockerfile                  # Python 3.11-slim container
├── docker-compose.yml          # App + Ollama (GPU) orchestration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Ollama** — [Install Ollama](https://ollama.com/download)
- **NVIDIA GPU** (recommended: RTX 4060 or better with 8GB+ VRAM)
- **MongoDB Atlas** account (optional — app works without it using fallback data)

### 1. Clone the Repository

```bash
git clone https://github.com/SECE-24-28/healthwallet-ta-mlops-project.git
cd healthwallet-ta-mlops-project
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Ollama (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b

# MongoDB Atlas (optional)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=health_wallet

# MLflow
MLFLOW_TRACKING_URI=./mlflow_data

# App
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### 4. Start Ollama & Pull Model

```bash
# Start Ollama server
ollama serve

# Pull the model (in another terminal)
ollama pull deepseek-r1:7b
```

### 5. Run the Application

```bash
# Development mode with hot reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

---

## API Endpoints

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check (Ollama + MongoDB status) |
| `GET` | `/api/health/metrics` | Inference metrics (latency, throughput, errors) |
| `GET` | `/api/health/models` | List available Ollama models |

### Medical Vault

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/vault/records` | List all medical records |
| `POST` | `/api/vault/records` | Create a new medical record |
| `POST` | `/api/vault/upload` | Upload prescription image (OCR extraction) |
| `DELETE` | `/api/vault/records/{id}` | Delete a medical record |

### AI Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message & get AI response |
| `GET` | `/api/chat/stream` | Stream AI response via SSE |

### Care Router

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/care/route` | Route patient to specialist |
| `POST` | `/api/care/anonymize` | Anonymize patient data (strip PII) |

---

## MLOps Pipeline

### Experiment Tracking (MLflow)

Every inference run is automatically logged to MLflow:

- **Parameters**: model name, prompt version, endpoint, success status
- **Metrics**: latency (ms), token count, tokens/sec throughput
- **Artifacts**: prompt text, response text (truncated to 2KB)

Access MLflow UI:
```bash
mlflow ui --backend-store-uri ./mlflow_data
```

### Inference Monitoring

The built-in monitor tracks a rolling window of 1000 inference events:

- **Latency percentiles**: P50, P95, P99
- **Throughput**: tokens/sec average, requests/min
- **Error rate**: percentage of failed inferences
- **Per-model stats**: breakdown by model name

Access via: `GET /api/health/metrics`

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
pytest tests/test_model.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## Docker Deployment

### Using Docker Compose (recommended)

```bash
# Build and start (with GPU support for Ollama)
docker-compose up --build

# Run in background
docker-compose up --build -d
```

This starts:
- **App container** — FastAPI backend + frontend on port `8000`
- **Ollama container** — Local LLM server on port `11434` (with NVIDIA GPU passthrough)

### Using Docker only

```bash
# Build
docker build -t health-wallet .

# Run
docker run -p 8000:8000 --env-file .env health-wallet
```

> **Note**: Docker Compose GPU configuration requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

---

## Team

**SECE-24-28** — Guru Aravinth S || Dineshkumar S

---

