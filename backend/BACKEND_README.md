# 🐍 FormPilot AI — Backend Service Documentation

> **Note**: This file is a mirror of [`backend/README.md`](./backend/README.md).

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql)](https://postgresql.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Graph-FF6F61.svg)](https://langchain.com)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33.svg?logo=playwright)](https://playwright.dev)

The **FormPilot AI Backend** is an asynchronous Python application powered by **FastAPI**, **LangGraph**, **SQLAlchemy 2.0 (asyncpg)**, and **Playwright Chromium**. It handles authentication, profile storage, multi-agent orchestration, form discovery, DOM extraction, field mapping, form filling, and real-time WebSocket event streaming.

---

## 📋 Table of Contents

- [Backend Architecture](#-backend-architecture)
- [Directory Structure](#-directory-structure)
- [LangGraph Agent Pipeline](#-langgraph-agent-pipeline)
- [Search & Discovery Service (`app/search`)](#-search--discovery-service-appsearch)
- [Browser Automation & Platform Adapters (`app/browser`)](#-browser-automation--platform-adapters-appbrowser)
- [Database Schema & Models](#-database-schema--models)
- [API Endpoints Reference](#-api-endpoints-reference)
- [WebSocket Event Protocol](#-websocket-event-protocol)
- [Local Test Forms](#-local-test-forms)
- [Setup & Environment Variables](#-setup--environment-variables)

---

## 📐 Backend Architecture

```
                                ┌────────────────────────┐
                                │   FastAPI Router Layer │
                                └───────────┬────────────┘
                                            │
                               ┌────────────┴────────────┐
                               │ Application Service Layer│
                               └────────────┬────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │                            │                            │
    ┌──────────▼──────────┐      ┌──────────▼──────────┐      ┌──────────▼──────────┐
    │ LangGraph Engine    │      │ SQLAlchemy Async    │      │  Playwright Browser │
    │ (Multi-Agent Graph) │      │ (PostgreSQL 16)     │      │ (Chromium Automation)
    └──────────┬──────────┘      └─────────────────────┘      └─────────────────────┘
               │
   ┌───────────┴───────────┐
   │ Search & Discovery    │
   │ (DDG + Trust Scorer)  │
   └───────────────────────┘
```

---

## 📁 Directory Structure

```
backend/
├── alembic/                    # Database migration scripts
│   ├── versions/               # Schema migration files
│   └── env.py
├── app/
│   ├── agents/                 # LangGraph Agent Nodes & State
│   │   ├── clarification_agent.py  # Asks user for missing inputs
│   │   ├── extraction_agent.py   # DOM field extractor JS injection
│   │   ├── filling_agent.py      # Playwright field interaction engine
│   │   ├── graph.py              # StateGraph definition & compiled singleton
│   │   ├── intent_agent.py       # Pydantic LLM intent parser
│   │   ├── mapping_agent.py      # Semantic profile-to-form field mapper
│   │   ├── navigation_agent.py   # Playwright page loading & login detection
│   │   ├── profile_retrieval_agent.py # Data-minimisation section retriever
│   │   ├── review_agent.py       # Confidence-tier review payload builder
│   │   ├── search_agent.py       # Multi-query DDG discovery & ranking node
│   │   ├── state.py              # AgentState TypedDict definition
│   │   └── validation_agent.py   # HTML5 constraint validation node
│   ├── browser/                # Browser automation layer
│   │   ├── manager.py            # Playwright browser instance manager & login detector
│   │   └── adapters/             # Platform-specific form adapters
│   │       ├── base.py           # BaseAdapter interface
│   │       ├── greenhouse.py     # Greenhouse.io adapter
│   │       └── lever.py          # Lever.co adapter
│   ├── core/                   # Core application configurations
│   │   ├── config.py             # BaseSettings environment configuration
│   │   ├── database.py           # Async engine & session factory
│   │   └── security.py           # Bcrypt hashing & JWT utilities
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── address.py            # Address table
│   │   ├── application.py        # ApplicationSession, JobSearchResult, etc.
│   │   ├── auth_tokens.py       # UserSession & token tables
│   │   ├── certifications.py     # Certification table
│   │   ├── documents.py          # Document table
│   │   ├── education.py          # Education table
│   │   ├── experience.py         # Experience table
│   │   ├── preferences.py        # JobPreference table
│   │   ├── professional_links.py # ProfessionalLink table
│   │   ├── profile.py            # UserProfile table
│   │   ├── projects.py           # Project table
│   │   ├── skills.py             # Skill table
│   │   └── user.py               # User core model
│   ├── routers/                # FastAPI endpoint handlers
│   │   ├── applications.py       # Job application workflow API
│   │   ├── auth.py               # Auth & JWT endpoints
│   │   ├── documents.py          # Document storage endpoints
│   │   ├── health.py             # System health check
│   │   ├── onboarding.py         # 10-step wizard API
│   │   ├── profile.py            # Profile CRUD endpoints
│   │   ├── settings.py           # Account settings & session management
│   │   └── ws.py                 # WebSocket event streaming
│   ├── schemas/                # Pydantic DTO validation schemas
│   ├── search/                 # Form/Job discovery package
│   │   ├── duckduckgo.py         # Rate-limited async DDG search wrapper
│   │   ├── query_builder.py      # Search term generator
│   │   ├── ranking.py            # Content relevance ranker
│   │   └── verifier.py           # Domain trust & safety verifier
│   ├── services/               # Application business logic
│   │   ├── application_service.py # Orchestrates session graph & DB persistence
│   │   └── settings_service.py    # Account settings & data export logic
│   ├── deps.py                 # Dependency injectors (get_db, get_current_user)
│   └── main.py                 # FastAPI application factory & lifespan
├── test_forms/                 # HTML test forms served in development
│   ├── dynamic_form.html
│   ├── multi_page_form.html
│   ├── repeated_sections_form.html
│   ├── simple_form.html
│   └── validation_form.html
├── alembic.ini
└── requirements.txt
```

---

## 🤖 LangGraph Agent Pipeline

The core agent framework uses **LangGraph** with `AgentState` TypedDict and structured output parsing.

### Workflow Nodes

1. **`parse_request`** (`intent_agent.py`):
   Extracts `intent` (`search_and_apply`, `open_and_apply`, `fill_only`, `continue_application`), target company, role, location, and skills using `gpt-4o-mini` with Pydantic structured output.

2. **`search_jobs` & `rank_results`** (`search_agent.py`):
   Invokes `app.search` to construct queries, search DuckDuckGo, score domain trust, and rank listings. Yields execution to user selection (`show_results`).

3. **`open_job_page`** (`navigation_agent.py`):
   Navigates to the job URL via Playwright, checking for login walls, CAPTCHAs, or OTP requirements. Yields control (`wait_for_login`) if manual authentication is needed.

4. **`extract_form`** (`extraction_agent.py`):
   Injects JavaScript to scan inputs, textareas, selects, and custom comboboxes. Extracts labels using priority:
   `label[for]` > `aria-label` > `aria-labelledby` > `placeholder` > `name` > `id` > container text.

5. **`load_user_profile`** (`profile_retrieval_agent.py`):
   Enforces **data minimisation** (PRD §12). Determines which profile sections are needed based on detected field labels and retrieves only those sections into state.

6. **`map_profile_fields`** (`mapping_agent.py`):
   Maps extracted fields to user profile JSON attributes with confidence scores (`0.0 - 1.0`) and statuses (`ready`, `missing`, `ambiguous`, `sensitive`, `unsupported`).

7. **`detect_missing`** (`clarification_agent.py`):
   Constructs human-friendly questions for missing or ambiguous required fields. Yields execution (`ask_user`) for user answers.

8. **`fill_form`** (`filling_agent.py`):
   Interacts directly with the page DOM via Playwright. Fills inputs, selects dropdown items, checks radio buttons, and invokes platform adapter pre/post hooks.

9. **`validate_form`** (`validation_agent.py`):
   Checks DOM elements against validation rules (maxlength, regex patterns, required) and logs errors.

10. **`prepare_review`** (`review_agent.py`):
    Builds the structured review payload grouped into confidence tiers (`auto_filled`, `highlighted`, `user_provided`, `low_confidence`, `missing`, `sensitive`) and determines if blocking issues remain.

---

## 🔍 Search & Discovery Service (`app/search`)

- **`query_builder.py`**: Accepts structured intent and generates up to 5 distinct queries (`site:company.com careers "Role"`, `company role apply`, `role skill location`).
- **`duckduckgo.py`**: Executes DDG text searches asynchronously in a thread pool. Implements exponential backoff on HTTP 429 rate-limits.
- **`verifier.py`**: Computes domain trust scores:
  - **Official Company Domains**: +40 trust boost.
  - **Trusted ATS Domains**: `greenhouse.io`, `lever.co`, `workday.com`, `myworkdayjobs.com`, `taleo.net`, `icims.com`, `smartrecruiters.com`, `bamboohr.com`, `ashbyhq.com`.
  - **Aggregators**: `linkedin.com`, `naukri.com`, `indeed.com`, `internshala.com`, `wellfound.com`.
  - **Filters**: Flags spam patterns and closed/expired postings.
- **`ranking.py`**: Evaluates title/snippet matches against role, company, location, skills, and domain trust score to rank listings on a scale of `0.0 – 100.0`.

---

## 🌐 Browser Automation & Platform Adapters (`app/browser`)

- **`BrowserManager`**: Manages Playwright Chromium instances. Keeps isolated browser contexts per application session.
- **`LoginDetector`**: Scans page for password fields, reCAPTCHA/hCaptcha, and OTP inputs.
- **`GreenhouseAdapter`**: Auto-expands education/employment sections, handles hidden file input elements, and flags EEOC/demographic fields for human review.
- **`LeverAdapter`**: Handles React form mounting delays, drag-and-drop file upload zones, referral source inputs, and social link mappings.

---

## 🗄️ Database Schema & Models

PostgreSQL 16 database managed via SQLAlchemy 2.0 async ORM and Alembic migrations.

- `users`: Core account details (`id`, `full_name`, `email`, `password_hash`, `is_active`, `is_email_verified`, `setup_complete`).
- `user_profiles`: Demographic information (`date_of_birth`, `gender`, `nationality`).
- `addresses`: Home & mailing addresses (`address_type`, `street`, `city`, `state`, `country`, `postal_code`).
- `education`: Academic history (`institution_name`, `degree`, `specialisation`, `start_date`, `end_date`, `cgpa`).
- `experience`: Work history (`company_name`, `job_title`, `employment_type`, `start_date`, `end_date`, `is_current`, `description`).
- `skills`: Skill names and proficiency levels.
- `projects`: Portfolio projects with URL links.
- `certifications`: Professional certifications and issuing organizations.
- `job_preferences`: Desired roles, locations, notice period, and minimum salary.
- `professional_links`: Social links (LinkedIn, GitHub, Portfolio).
- `documents`: Document vault file metadata (`document_type`, `original_filename`, `storage_path`, `is_default`).
- `application_sessions`: Application workflow session state, intent, current URL, node status, browser context mapping.
- `job_search_results`: Ranked job discovery candidates.
- `detected_form_fields`: Extracted HTML elements.
- `field_mappings`: Mapped profile values with confidence scores.
- `missing_questions`: Clarification questions for unmapped fields.
- `user_answers`: User answers supplied during clarification flow.
- `validation_errors`: Post-fill constraint violations.
- `user_sessions`: Active refresh token sessions.

---

## 🔌 API Endpoints Reference

### Authentication Router (`/api/auth`)
- `POST /api/auth/register` — Create user account
- `POST /api/auth/login` — Authenticate and receive access/refresh tokens
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/logout` — Revoke refresh token
- `GET /api/auth/verify-email?token=...` — Verify email via token
- `POST /api/auth/forgot-password` — Request password reset email
- `POST /api/auth/reset-password` — Reset password via token

### Profile Management Router (`/api/profile`)
- `GET /api/profile` — Fetch complete profile JSON
- `PUT /api/profile/personal` — Update personal details
- `GET /api/profile/completion` — Calculate completion percentage
- `GET|POST|PUT|DELETE /api/profile/education` — Education history CRUD
- `GET|POST|PUT|DELETE /api/profile/experience` — Experience history CRUD
- `GET|POST|PUT|DELETE /api/profile/skills` — Skills CRUD
- `GET|POST|PUT|DELETE /api/profile/projects` — Projects CRUD
- `GET|POST|PUT|DELETE /api/profile/certifications` — Certifications CRUD
- `GET|POST|PUT|DELETE /api/profile/addresses` — Addresses CRUD
- `GET|PUT /api/profile/preferences` — Job preferences
- `GET|POST|PUT|DELETE /api/profile/professional-links` — Social links CRUD

### Document Vault Router (`/api/documents`)
- `GET /api/documents` — List user documents
- `POST /api/documents/upload` — Upload resume/document file (`multipart/form-data`)
- `GET /api/documents/{id}/download` — Download stored document file
- `DELETE /api/documents/{id}` — Delete document
- `PATCH /api/documents/{id}/default` — Mark resume as default

### Application Session Router (`/api/applications`)
- `POST /api/applications/start` — Initialize session with prompt or URL
- `GET /api/applications` — List user application sessions
- `GET /api/applications/{session_id}` — Get session status & details
- `POST /api/applications/{session_id}/search` — Trigger agent search phase
- `GET /api/applications/{session_id}/jobs` — Fetch ranked job search results
- `POST /api/applications/{session_id}/select-job` — Select target job result
- `POST /api/applications/{session_id}/job-url` — Submit direct job URL
- `POST /api/applications/{session_id}/continue` — Resume session after manual action
- `POST /api/applications/{session_id}/stop` — Stop session & close browser
- `GET /api/applications/{session_id}/browser-status` — Check browser status
- `GET /api/applications/{session_id}/questions` — Get missing field questions
- `POST /api/applications/{session_id}/answers` — Submit answers to questions
- `GET /api/applications/{session_id}/review` — Get review summary payload
- `PATCH /api/applications/{session_id}/fields/{field_id}` — Override mapped field value
- `POST /api/applications/{session_id}/validate` — Re-validate form fields

### Settings Router (`/api/settings`)
- `GET /api/settings/account` — Get account metadata
- `PATCH /api/settings/account/name` — Update display name
- `POST /api/settings/account/change-password` — Change password
- `GET /api/settings/sessions` — List active refresh sessions
- `DELETE /api/settings/sessions/{session_id}` — Revoke session
- `POST /api/settings/sessions/revoke-all` — Revoke all sessions
- `GET /api/settings/data-export` — Download full JSON export of user data
- `DELETE /api/settings/account` — Permanently delete account

---

## 📡 WebSocket Event Protocol

Endpoint: `ws://localhost:8000/ws/applications/{session_id}?token={access_token}`

Emits JSON events during agent execution:
- `agent_message`: `{ "type": "agent_message", "node": "search_jobs", "text": "Searching..." }`
- `jobs_found`: `{ "type": "jobs_found", "count": 8 }`
- `fields_extracted`: `{ "type": "fields_extracted", "count": 14 }`
- `mapping_complete`: `{ "type": "mapping_complete", "ready": 10, "missing": 2, "ambiguous": 2 }`
- `manual_action_required`: `{ "type": "manual_action_required", "reason": "login_required" }`
- `review_ready`: `{ "type": "review_ready", "can_proceed": true }`
- `ping`: Keepalive ping emitted every 15 seconds.

---

## 🧪 Local Test Forms

The backend serves mock HTML application forms under `http://localhost:8000/test-forms/`:
- `simple_form.html`: Standard basic form.
- `dynamic_form.html`: Role-type selection dynamically shows/hides conditional fields.
- `repeated_sections_form.html`: Dynamic add/remove entry controls for education & experience.
- `validation_form.html`: Real-time character counters, pattern checks, password strength meter.
- `multi_page_form.html`: Multi-step form navigation.

---

## ⚙️ Setup & Environment Variables

### 1. Requirements
- Python 3.11+
- PostgreSQL 16 server running on localhost or remote host

### 2. Environment Configuration (`backend/.env`)

```env
APP_NAME="FormPilot AI"
APP_ENV="development"
DEBUG=True

DATABASE_URL="postgresql+asyncpg://formpilot:formpilot@localhost:5432/formpilot"

SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

OPENAI_API_KEY="sk-proj-..."
OPENAI_MODEL="gpt-4o-mini"

FRONTEND_URL="http://localhost:5173"
CORS_ORIGINS="http://localhost:5173"

UPLOAD_DIR="uploads"
MAX_UPLOAD_SIZE_MB=5
```

### 3. Installation Commands

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```
