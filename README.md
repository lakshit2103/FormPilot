# 🤖 FormPilot AI — Autonomous Job Application Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg?logo=react)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql)](https://postgresql.org)

**FormPilot AI** is an autonomous, multi-agent AI web application designed to automate tedious career application forms. Given a natural-language search query (e.g., *"Find and fill the TCS application form for an Agentic AI Engineer role"*), FormPilot AI automatically searches relevant job portals, extracts dynamic form schemas using headless browser automation, maps your personal profile and uploaded documents onto form fields, collects any missing details, and prepares a verified application for human-in-the-loop review.

---

## 🌟 Key Highlights

- 🔍 **Natural Language Job Requests**: Type any career search prompt to discover official and 3rd-party job listings ranked by relevance.
- 🤖 **LangGraph Multi-Agent Pipeline**: Dedicated AI agents handle intent parsing, DuckDuckGo job search, DOM extraction, field mapping, and validation.
- ⚡ **10-Step Onboarding Profile Vault**: Comprehensive reusable profile manager covering Personal details, Addresses, Education, Work Experience, Skills, Projects, Certifications, Job Preferences, Social Links, and Documents.
- 📄 **Smart Document Storage**: Upload and manage resumes, cover letters, and certificates (`.pdf`, `.docx`, `.jpg`) that seamlessly link to application forms.
- 🔒 **Human-in-the-Loop Safety Guarantee**: FormPilot AI **never submits forms automatically**. The agent fills and validates fields, then yields control to you for final submission.
- 🎨 **FactoryOS Parchment Design System**: Styled with a high-contrast industrial UI theme (`#f4f2eb`, `--brand: #1d5c7a`, glass cards) and responsive components.

---

## 📐 Multi-Agent Graph Architecture

```
                       [ Natural Language Request ]
                                    │
                                    ▼
                         ┌────────────────────┐
                         │   Intent Agent     │  ── Extracts Target Company, Role & Criteria
                         └──────────┬─────────┘
                                    ▼
                         ┌────────────────────┐
                         │   Search Agent     │  ── Searches DuckDuckGo & Ranks Listings
                         └──────────┬─────────┘
                                    ▼
                         ┌────────────────────┐
                         │  Extraction Agent  │  ── Playwright Headless DOM Inspection
                         └──────────┬─────────┘
                                    ▼
                         ┌────────────────────┐
                         │   Mapping Agent    │  ── Maps User Profile & Resumes to Form
                         └──────────┬─────────┘
                                    ▼
                         ┌────────────────────┐
                         │  Validation Agent  │  ── Detects Missing Fields & Triggers Review
                         └────────────────────┘
```

---

## 🚀 Application Workflow & Screens

1. **Dashboard (Screen 03)**: Natural language prompt box, quick application stats grid, recent activity table, and profile completion tracking.
2. **Onboarding Wizard (10 Steps)**: Step-by-step setup featuring country code flag selectors (`🇮🇳 +91`, `🇺🇸 +1`), education/experience forms, skill tags, and document uploads.
3. **Job Search Results (Screen 05)**: Ranked search results displaying official vs 3rd-party badges, relevance score, direct links, and manual URL fallback.
4. **Progress Monitor (Screen 06)**: 7-stage workflow stepper, live browser status, manual action lock banners, and real-time agent log feed over WebSockets.
5. **Missing Information (Screen 07)**: Dynamic question cards for fields not present in your profile, with options to save answers back to your profile.
6. **Review Dashboard (Screen 08)**: Comprehensive audit table showing auto-filled fields, source mapping, confidence metrics, inline field editing, and revalidation.

---

## 💻 Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite | Fast SPA with zero-dependency Vanilla CSS Design System |
| **Backend** | Python 3.11, FastAPI, Uvicorn | Asynchronous REST & WebSocket server |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 | Async ORM with Alembic schema migrations |
| **AI Agents** | LangGraph, OpenAI / LLMs | Stateful multi-agent graph orchestration |
| **Automation** | Playwright Chromium | Headless browser form discovery and field interaction |
| **Authentication** | JWT, Bcrypt, SMTP Email | Access/Refresh token rotation and email verification |

---

## 🔌 API Endpoint Summary

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Create user account & send verification email
- `POST /api/auth/login` — Sign in and receive JWT tokens
- `GET /api/auth/verify-email` — Verify account email via token
- `POST /api/auth/refresh` — Rotate access token using refresh token

### Profile Management (`/api/profile`)
- `GET /api/profile` & `PUT /api/profile` — Fetch/Update personal & contact details
- `GET /api/profile/completion` — Calculate overall readiness percentage
- `GET|POST|DELETE /api/profile/education` — Education history CRUD
- `GET|POST|DELETE /api/profile/experience` — Work experience CRUD
- `GET|POST|DELETE /api/profile/skills` — Skills manager CRUD
- `GET|POST|DELETE /api/profile/projects` — Portfolio projects CRUD
- `GET|POST|DELETE /api/profile/certifications` — Certifications CRUD
- `GET|POST|DELETE /api/profile/addresses` — User address CRUD
- `GET|PUT /api/profile/preferences` — Job search preferences
- `GET|POST|DELETE /api/profile/professional-links` — Social links CRUD

### Document Vault (`/api/documents`)
- `GET /api/documents` — List uploaded documents
- `POST /api/documents/upload` — Upload resume or document
- `GET /api/documents/{id}/download` — Download document file
- `PATCH /api/documents/{id}/default` — Set primary default resume

### Application Sessions (`/api/applications`)
- `POST /api/applications/start` — Start new job application session
- `GET /api/applications/{id}/jobs` — Fetch ranked job search results
- `POST /api/applications/{id}/select-job` — Select target job listing
- `WS /api/applications/{id}/ws` — Real-time agent status & logs
- `GET /api/applications/{id}/review` — Fetch review mapping audit
- `PATCH /api/applications/{id}/fields/{field_id}` — Manually edit mapped field value

---

## 🛠️ Quick Start & Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/lakshit2103/FormPilot.git
cd FormPilot
```

### 2. Configure Backend Environment

Copy `.env.example` to `backend/.env`:
```bash
cp .env.example backend/.env
```

Update your `backend/.env` with your settings:
```env
DATABASE_URL=postgresql+asyncpg://formpilot:formpilot@127.0.0.1:5433/formpilot
SECRET_KEY=generate_with_python_secrets
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_id@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### 3. Start PostgreSQL Database

```bash
docker compose up -d
```

### 4. Run Backend Server

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

### 5. Run Frontend Development Server

In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
- **Frontend App**: `http://localhost:5173`

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more details.
