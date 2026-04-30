# 📞 Intelligent Call QA Platform

> **Bachelor's Thesis — Civil Computer Engineering · UNAB Santiago, 2026**
> *Felipe Vergara · felipe.vergara19@gmail.com*

**[🇪🇸 Versión en Español](README.es.md)**

---

An AI-powered quality assurance platform for call-center collections (cobranza) operations at **Colektia**. The system automatically ingests call recordings, transcribes them, and audits them against configurable rubrics using **Google Gemini 2.5 Flash**, delivering real-time QA metrics through a React dashboard.

## ✨ Key Features

- **Automatic AI Auditing** — Evaluates calls against dynamic rubrics with configurable criteria, weights, and severity flags
- **Micro-batch Processing** — Ingestion and AI evaluation are fully decoupled; a scheduler runs every 240 minutes to process pending calls in batches of 100
- **Human-in-the-Loop** — Analysts can approve, reject, or comment on AI-generated evaluations
- **Role-based Access Control** — Four roles: Admin, QA Analyst, KAM, Client
- **Multi-tenant Architecture** — Data isolation per client company (Sistecredito, Rapicredit, etc.)
- **Live KPI Dashboard** — Coverage %, average quality score, status distribution, and more
- **Flexible Rubrics** — Create rubrics per company and delinquency range (days overdue)
- **Prompt Tuning** — Update the AI base prompt in real time without redeployment

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLModel · APScheduler |
| Database | PostgreSQL |
| AI | Google Gemini 2.5 Flash (via `google-generativeai`) |
| Frontend | React 18 · Vite · Tailwind CSS |
| Auth | JWT (Sprint 3 — in progress) |

## 🗂️ Project Structure

```
Qa_llamadas/
├── backend/
│   ├── main.py          # FastAPI app, endpoints, scheduler (HU05, HU16, HU17…)
│   ├── models.py        # SQLModel table definitions (8 tables)
│   ├── services.py      # Gemini AI auditing logic with retry
│   ├── schemas.py       # Pydantic ingestion schemas
│   └── database.py      # Engine & session setup
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── Dashboard.jsx    # Call history + KPIs
│       │   ├── CallDetail.jsx   # Full audit detail per call
│       │   └── Settings.jsx     # Rubrics & prompt configuration
│       └── api.js               # Axios API client
└── ERD_QA_Llamadas.pdf  # Entity-Relationship Diagram
```

## 🗄️ Database Schema (8 tables)

| Table | Purpose |
|---|---|
| `usuario` | Authentication & roles (admin / analista_qa / kam / cliente) |
| `cliente` | Client companies with their call scripts |
| `llamada` | Call records with transcription and metadata |
| `evaluacion` | AI audit results + human validation fields |
| `rubrica` | Evaluation rubrics per company and delinquency range |
| `criterio` | Individual criteria within a rubric (weight + severity) |
| `configuracionsistema` | Key-value system config (AI base prompt, etc.) |
| `guioncliente` | Client scripts — reserved for Sprint 4 (HU25) |

> See [`ERD_QA_Llamadas.pdf`](ERD_QA_Llamadas.pdf) for the full entity-relationship diagram.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally
- A Google Gemini API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/qa_llamadas"
export GEMINI_API_KEY="your-api-key-here"

uvicorn main:app --reload
```

API available at `http://localhost:8000` · Docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

## 📡 Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/llamadas/ingesta` | Ingest a new call (from Colly) |
| `POST` | `/api/v1/auditoria/ejecutar` | Manually trigger the audit batch |
| `GET` | `/api/v1/auditoria/estado` | Queue status + next scheduled run |
| `GET` | `/api/v1/llamadas` | Full call history |
| `GET` | `/api/v1/evaluaciones/{id}` | Detailed audit result for a call |
| `GET` | `/api/v1/dashboard` | Global KPIs |
| `GET/POST` | `/api/v1/rubricas` | List / create rubrics |
| `GET/POST` | `/api/v1/config/prompt` | Get / update AI base prompt |

## 📋 Development Progress

| Sprint | Dates | Points | Status |
|---|---|---|---|
| Sprint 1 | Mar 01 – Mar 14 2026 | 22 pts | ✅ Done |
| Sprint 2 | Mar 15 – Apr 11 2026 | 34 pts | ✅ Done |
| Sprint 3 | Apr 26 – May 09 2026 | 26 pts | 🔄 In Progress |
| Sprint 4 | May 10 – May 16 2026 | 21 pts | ⏳ Pending |
| Sprint 5 | May 17 – May 19 2026 | 18 pts | ⏳ Final delivery |

## 📄 License

Academic project — Universidad Andrés Bello (UNAB), Santiago, Chile.
Not licensed for commercial use.
