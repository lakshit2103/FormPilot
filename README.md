# 🤖 FormPilot AI — Autonomous Web Form Discovery, Understanding & Filling Agent

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql)](https://postgresql.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Graph-FF6F61.svg)](https://langchain.com)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33.svg?logo=playwright)](https://playwright.dev)

> 📖 **Sub-System Documentation**:
> - 🐍 [**Backend Documentation & API Reference**](./backend/README.md) — Detailed agent pipeline, search service, database models, and API endpoints.
> - ⚡ [**Frontend Documentation & Route Reference**](./frontend/README.md) — Single page app architecture, state management, routes, and UI design system.

**FormPilot AI** is an agentic AI system and secure web application designed to help users discover, understand, navigate, and complete online form applications—including job portals (Workday, Greenhouse, Lever, etc.), university admissions, registration portals, and government standard forms. 

> **Core Operating Principle**: The AI discovers, extracts, maps, and fills supported form fields, but **the user remains in absolute control of identity, sensitive data, declarations, payments, and final submission**. FormPilot AI will **never** submit a form automatically.

---

## 📋 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [LangGraph Agent Pipeline](#-langgraph-agent-pipeline)
- [Project Directory Structure](#-project-directory-structure)
- [Backend Documentation](#-backend-documentation)
  - [Database Models & Schemas](#database-models--schemas)
  - [Discovery & Search Engine (`app/search`)](#discovery--search-engine-appsearch)
  - [Platform Adapters (`app/browser/adapters`)](#platform-adapters-appbrowseradapters)
  - [Exhaustive API Endpoint Reference](#exhaustive-api-endpoint-reference)
  - [WebSocket Streaming (`/ws/applications/{session_id}`)](#websocket-streaming-wsapplicationssession_id)
  - [Local Test Forms](#local-test-forms)
- [Frontend Documentation](#-frontend-documentation)
  - [State Management & API Layer](#state-management--api-layer)
  - [Route Guards & Authentication Flow](#route-guards--authentication-flow)
  - [Exhaustive Frontend Route Reference](#exhaustive-frontend-route-reference)
- [Local Installation & Development Setup](#-local-installation--development-setup)

---

## 📐 Architectural Overview

```
                      ┌─────────────────────────────────────────┐
                      │              React 19 SPA               │
                      │  (Vite + TypeScript + Vanilla CSS UI)   │
                      └────────────────────┬────────────────────┘
                                           │
                                ┌──────────┴──────────┐
                                │ REST APIs / WebSockets │
                                └──────────┬──────────┘
                                           │
                      ┌────────────────────▼────────────────────┐
                      │             FastAPI Backend             │
                      │   (Python 3.11 + Async SQLAlchemy)      │
                      └───────┬─────────────────────────┬───────┘
                              │                         │
            ┌─────────────────▼────────┐       ┌────────▼────────────────┐
            │   PostgreSQL 16 DB       │       │    LangGraph Engine     │
            │ (User Vault & Sessions)  │       │ (Stateful Agent Graph) │
            └──────────────────────────┘       └────────┬────────────────┘
                                                        │
                                               ┌────────▼────────────────┐
                                               │ Playwright Automation   │
                                               │ (Chromium Browser Manager)
                                               └─────────────────────────┘
```

---

## 🤖 LangGraph Agent Pipeline

The core agent framework uses **LangGraph** with structured Pydantic schemas and `gpt-4o-mini` (with rule-based offline fallbacks).

```
[ parse_request ]
        │
        ├─► [ search_jobs ] ──► [ rank_results ] ──► [ show_results ] (PAUSE: User selects listing)
        │                                                     │
        ├─► (URL Provided) ───────────────────────────────────┘
        │
        ▼
[ open_job_page ] ──► (Login / CAPTCHA detected?) ──► [ wait_for_login ] (PAUSE: User logs in)
        │
        ▼
[ extract_form ] ──► [ load_user_profile ] ──► [ map_profile_fields ] ──► [ detect_missing ]
                                                                                   │
                                     (Missing / Ambiguous fields?) ────────────────┼──► [ ask_user ] (PAUSE)
                                                                                   │
[ complete_session ] ◄── [ prepare_review ] ◄── [ validate_form ] ◄── [ fill_form ] ◄───┘
```

### Agent Nodes & Responsibilities

1. **`parse_request`** (`intent_agent.py`): Parses natural-language user prompts to extract structured intent (`search_and_apply`, `open_and_apply`, `fill_only`, `continue_application`), target company, role, location, and skills.
2. **`search_jobs` & `rank_results`** (`search_agent.py`): Uses `app.search` to construct queries, query DuckDuckGo with rate-limit retries, verify domain trust, and rank listings by relevance.
3. **`open_job_page`** (`navigation_agent.py`): Launches Chromium via Playwright, navigates to the target URL, and checks for login wall/CAPTCHA/OTP requirement.
4. **`extract_form`** (`extraction_agent.py`): Injects DOM inspection JS to extract all visible fields, label priorities (`label[for] > aria-label > placeholder > name > id`), field types, select options, and HTML5 validation constraints.
5. **`load_user_profile`** (`profile_retrieval_agent.py`): Implements **data-minimisation** (PRD §12). Analyses field labels to load only the required profile sections into agent memory.
6. **`map_profile_fields`** (`mapping_agent.py`): Uses LLM structured output to map detected fields to profile JSON paths with confidence scores (0.0–1.0) and status assignment (`ready`, `missing`, `ambiguous`, `sensitive`, `unsupported`).
7. **`detect_missing` & `ask_user`** (`clarification_agent.py`): Identifies unmapped or ambiguous required fields and constructs simple human-facing questions.
8. **`fill_form`** (`filling_agent.py`): Interacts with DOM via Playwright. Fills text inputs, selects dropdown items, clicks radio buttons, and handles platform adapter hooks.
9. **`validate_form`** (`validation_agent.py`): Checks DOM element values against HTML constraints (regex, min/max length, required) and logs errors.
10. **`prepare_review`** (`review_agent.py`): Groups mappings into confidence tiers (`auto_filled`, `highlighted`, `user_provided`, `low_confidence`, `missing`, `sensitive`) and determines whether the form is ready for human approval.

---

## 📁 Project Directory Structure

```
FormPilot/
├── backend/
│   ├── alembic/                    # Alembic DB migration scripts
│   ├── app/
│   │   ├── agents/                 # LangGraph multi-agent nodes & graph state
│   │   │   ├── clarification_agent.py
│   │   │   ├── extraction_agent.py
│   │   │   ├── filling_agent.py
│   │   │   ├── graph.py            # Main StateGraph orchestration
│   │   │   ├── intent_agent.py
│   │   │   ├── mapping_agent.py
│   │   │   ├── navigation_agent.py
│   │   │   ├── profile_retrieval_agent.py
│   │   │   ├── review_agent.py
│   │   │   ├── search_agent.py
│   │   │   ├── state.py            # AgentState TypedDict definition
│   │   │   └── validation_agent.py
│   │   ├── browser/                # Playwright automation layer
│   │   │   ├── manager.py          # BrowserManager & LoginDetector
│   │   │   └── adapters/           # Platform-specific form handling
│   │   │       ├── base.py
│   │   │       ├── greenhouse.py   # Greenhouse.io adapter
│   │   │       └── lever.py        # Lever.co adapter
│   │   ├── core/                   # Core application configuration
│   │   │   ├── config.py           # Pydantic BaseSettings
│   │   │   ├── database.py         # Async Engine & SessionMaker
│   │   │   └── security.py         # Bcrypt password hashing & JWT helpers
│   │   ├── models/                 # SQLAlchemy ORM Data Models
│   │   │   ├── address.py
│   │   │   ├── application.py
│   │   │   ├── auth_tokens.py
│   │   │   ├── certifications.py
│   │   │   ├── documents.py
│   │   │   ├── education.py
│   │   │   ├── experience.py
│   │   │   ├── preferences.py
│   │   │   ├── professional_links.py
│   │   │   ├── profile.py
│   │   │   ├── projects.py
│   │   │   ├── skills.py
│   │   │   └── user.py
│   │   ├── routers/                # FastAPI APIRouters
│   │   │   ├── applications.py
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── health.py
│   │   │   ├── onboarding.py
│   │   │   ├── profile.py
│   │   │   ├── settings.py
│   │   │   └── ws.py               # WebSocket real-time event router
│   │   ├── schemas/                # Pydantic Request/Response DTOs
│   │   ├── search/                 # Discovery & Ranking package
│   │   │   ├── duckduckgo.py       # Rate-limited DDG wrapper
│   │   │   ├── query_builder.py    # Query generator
│   │   │   ├── ranking.py          # Intent relevance scorer
│   │   │   └── verifier.py         # Domain trust & safety checker
│   │   ├── services/               # Core business services
│   │   │   ├── application_service.py
│   │   │   └── settings_service.py
│   │   ├── deps.py                 # FastAPI dependency injection
│   │   └── main.py                 # Application factory & lifespan
│   ├── test_forms/                 # Built-in test HTML forms
│   │   ├── dynamic_form.html
│   │   ├── multi_page_form.html
│   │   ├── repeated_sections_form.html
│   │   ├── simple_form.html
│   │   └── validation_form.html
│   ├── alembic.ini
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/                    # Axios API clients
    │   │   ├── applications.ts
    │   │   ├── auth.ts
    │   │   ├── client.ts           # Interceptor with automatic token refresh
    │   │   ├── documents.ts
    │   │   ├── profile.ts
    │   │   └── settings.ts
    │   ├── components/             # Reusable UI component library
    │   │   ├── auth/               # Route Guard wrapper components
    │   │   ├── layout/             # Topbar & Sidebar layout container
    │   │   └── ui/                 # Cards, Buttons, Inputs, Loaders, Toasts
    │   ├── features/               # Feature Page Modules
    │   │   ├── applications/       # Job Search, Progress, Questions, Review
    │   │   ├── auth/               # Login, Register, Email Verify, Password Reset
    │   │   ├── dashboard/          # Natural prompt bar, Stats, Recent Activity
    │   │   ├── documents/          # Document Vault & Resume Manager
    │   │   ├── landing/            # Public Landing Page
    │   │   ├── onboarding/         # 10-Step Onboarding Wizard
    │   │   ├── profile/            # Profile Manager Tabs
    │   │   └── settings/           # Account & Security Settings
    │   ├── stores/                 # Zustand Persistent Stores
    │   │   ├── applicationStore.ts
    │   │   └── authStore.ts
    │   ├── utils/
    │   ├── App.tsx                 # React Router v6 router configuration
    │   ├── index.css               # Global Design System CSS & variables
    │   └── main.tsx
    ├── index.html
    ├── package.json
    └── vite.config.ts
```

---

## ⚙️ Backend Documentation

### Database Models & Schemas

PostgreSQL 16 database accessed asynchronously via SQLAlchemy 2.0.

- **`User`** (`users`): Primary account entity (`id`, `full_name`, `email`, `password_hash`, `is_active`, `is_email_verified`, `setup_complete`).
- **`UserProfile`** (`user_profiles`): Demographic details (`date_of_birth`, `gender`, `nationality`, `summary`).
- **`Address`** (`addresses`): Residential addresses (`address_type`, `street`, `city`, `state`, `country`, `postal_code`).
- **`Education`** (`education`): Degree and academic background (`institution_name`, `degree`, `specialisation`, `start_date`, `end_date`, `cgpa`, `percentage`).
- **`Experience`** (`experience`): Work history (`company_name`, `job_title`, `employment_type`, `location`, `start_date`, `end_date`, `is_current`, `description`).
- **`Skill`** (`skills`): Professional skills & proficiency (`skill_name`, `proficiency_level`).
- **`Project`** (`projects`): Portfolio projects (`title`, `description`, `technologies`, `project_url`, `repository_url`).
- **`Certification`** (`certifications`): Certifications (`name`, `issuing_organization`, `issue_date`).
- **`JobPreference`** (`job_preferences`): Desired roles, locations, notice period, minimum salary, relocation preference.
- **`ProfessionalLink`** (`professional_links`): External profiles (`platform`, `url`).
- **`Document`** (`documents`): Document vault uploads (`document_type`, `original_filename`, `storage_path`, `is_default`).
- **`ApplicationSession`** (`application_sessions`): Active workflow session state, intent, current URL, node status, browser context mapping.
- **`JobSearchResult`** (`job_search_results`): Ranked job discovery candidates (`title`, `company`, `location`, `url`, `domain`, `relevance_score`, `is_official`, `job_status`).
- **`DetectedFormField`** (`detected_form_fields`): Raw extracted HTML elements (`field_identifier`, `field_type`, `label`, `placeholder`, `is_required`, `available_options`, `validation_constraints`).
- **`FieldMapping`** (`field_mappings`): Mapped profile values (`profile_key`, `proposed_value`, `confidence`, `mapping_status`, `reason`, `user_approved`).
- **`MissingQuestion`** (`missing_questions`): Questions generated for unmapped fields (`question`, `field_requirements`, `status`).
- **`UserAnswer`** (`user_answers`): User answers supplied during clarification flow (`answer_value`, `save_to_profile`).
- **`ValidationError`** (`validation_errors`): Post-fill constraint violations (`error_type`, `error_message`, `is_resolved`).
- **`UserSession`** (`user_sessions`): Active refresh token sessions for JWT rotation & device revocation.

---

### Discovery & Search Engine (`app/search`)

- **`query_builder.py`**: Accepts structured intent and generates up to 5 targeted search terms (e.g. `site:company.com careers "Role"`, `company role apply`, `role skill location`).
- **`duckduckgo.py`**: Executes DuckDuckGo text searches asynchronously using thread execution. Features exponential backoff (`3s -> 6s -> 12s`) when facing rate-limiting (`429`).
- **`verifier.py`**: Classifies URL domains:
  - **Official Company Domains**: +40 trust boost.
  - **Trusted ATS Domains**: `greenhouse.io`, `lever.co`, `workday.com`, `myworkdayjobs.com`, `taleo.net`, `icims.com`, `smartrecruiters.com`, `bamboohr.com`, `ashbyhq.com`.
  - **Aggregators**: `linkedin.com`, `naukri.com`, `indeed.com`, `internshala.com`, `wellfound.com`.
  - **Suspicious/Expired Filters**: Flags scam patterns or closed applications.
- **`ranking.py`**: Evaluates title/snippet matches against role, company, location, skills, and domain trust score to rank listings on a scale of `0.0 – 100.0`.

---

### Platform Adapters (`app/browser/adapters`)

Custom Playwright logic for platform-specific DOM behavior:
- **`GreenhouseAdapter`**: Auto-expands education/employment repeatable sections prior to extraction, maps styled upload containers to hidden `<input type="file">` elements, and flags EEOC/demographic sections for human review.
- **`LeverAdapter`**: Handles React form mounting delays, drag-and-drop file upload zones, referral source inputs, and social link mappings.

---

### Exhaustive API Endpoint Reference

#### 1. Authentication Router (`/api/auth`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Registers new account, hashes password, and creates verification token. |
| `POST` | `/api/auth/login` | No | Validates credentials and returns `access_token` and `refresh_token`. |
| `POST` | `/api/auth/refresh` | No | Rotates access token using a valid refresh token. |
| `POST` | `/api/auth/logout` | No | Revokes refresh token session. |
| `GET` | `/api/auth/verify-email` | No | Verifies user email via URL token. |
| `POST` | `/api/auth/forgot-password` | No | Generates password reset token. |
| `POST` | `/api/auth/reset-password` | No | Resets user password using reset token. |

#### 2. Profile Management Router (`/api/profile`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/profile` | Yes | Retrieves full user profile JSON (personal, contact, education, experience, etc.). |
| `PUT` | `/api/profile/personal` | Yes | Updates core personal details (full name, date of birth, gender, nationality). |
| `GET` | `/api/profile/completion` | Yes | Returns overall profile readiness percentage and per-section breakdown. |
| `GET` | `/api/profile/education` | Yes | Lists education records. |
| `POST` | `/api/profile/education` | Yes | Adds new education entry. |
| `PUT` | `/api/profile/education/{id}`| Yes | Updates existing education entry. |
| `DELETE`| `/api/profile/education/{id}`| Yes | Deletes education entry. |
| `GET` | `/api/profile/experience` | Yes | Lists work experience records. |
| `POST` | `/api/profile/experience` | Yes | Adds new work experience entry. |
| `PUT` | `/api/profile/experience/{id}`| Yes| Updates existing experience entry. |
| `DELETE`| `/api/profile/experience/{id}`| Yes| Deletes experience entry. |
| `GET` | `/api/profile/skills` | Yes | Lists skills records. |
| `POST` | `/api/profile/skills` | Yes | Adds new skill entry. |
| `PUT` | `/api/profile/skills/{id}` | Yes | Updates skill proficiency. |
| `DELETE`| `/api/profile/skills/{id}` | Yes | Deletes skill entry. |
| `GET` | `/api/profile/projects` | Yes | Lists portfolio projects. |
| `POST` | `/api/profile/projects` | Yes | Adds portfolio project. |
| `PUT` | `/api/profile/projects/{id}` | Yes | Updates project. |
| `DELETE`| `/api/profile/projects/{id}` | Yes | Deletes project. |
| `GET` | `/api/profile/certifications`| Yes | Lists certifications. |
| `POST` | `/api/profile/certifications`| Yes | Adds certification. |
| `PUT` | `/api/profile/certifications/{id}`| Yes| Updates certification. |
| `DELETE`| `/api/profile/certifications/{id}`| Yes| Deletes certification. |
| `GET` | `/api/profile/addresses` | Yes | Lists user addresses. |
| `POST` | `/api/profile/addresses` | Yes | Adds new address. |
| `PUT` | `/api/profile/addresses/{id}`| Yes | Updates address. |
| `DELETE`| `/api/profile/addresses/{id}`| Yes | Deletes address. |
| `GET` | `/api/profile/preferences`| Yes | Fetches job search preferences. |
| `PUT` | `/api/profile/preferences`| Yes | Updates job search preferences. |
| `GET` | `/api/profile/professional-links`| Yes | Lists professional links (LinkedIn, GitHub, Portfolio). |
| `POST` | `/api/profile/professional-links`| Yes | Adds professional link. |
| `PUT` | `/api/profile/professional-links/{id}`| Yes| Updates professional link. |
| `DELETE`| `/api/profile/professional-links/{id}`| Yes| Deletes professional link. |

#### 3. Document Vault Router (`/api/documents`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/documents` | Yes | Lists all uploaded user documents. |
| `POST` | `/api/documents/upload` | Yes | Uploads resume/document (`multipart/form-data`). |
| `GET` | `/api/documents/{id}/download` | Yes | Downloads stored document file. |
| `DELETE`| `/api/documents/{id}` | Yes | Deletes uploaded document. |
| `PATCH` | `/api/documents/{id}/default` | Yes | Sets document as default primary resume. |

#### 4. Onboarding Router (`/api/onboarding`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/onboarding/status` | Yes | Returns current onboarding step index and completion state. |
| `POST` | `/api/onboarding/step` | Yes | Saves payload for current onboarding step. |
| `POST` | `/api/onboarding/complete` | Yes | Marks onboarding setup complete (`setup_complete = true`). |

#### 5. Application Session Router (`/api/applications`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/applications/start` | Yes | Initializes application session with natural language prompt or URL. |
| `GET` | `/api/applications` | Yes | Lists user application sessions. |
| `GET` | `/api/applications/{session_id}` | Yes | Fetches session status & state summary. |
| `POST` | `/api/applications/{session_id}/search` | Yes | Triggers agent search phase for prompt. |
| `GET` | `/api/applications/{session_id}/jobs` | Yes | Returns ranked job search results. |
| `POST` | `/api/applications/{session_id}/select-job` | Yes | Selects target job listing from search results. |
| `POST` | `/api/applications/{session_id}/job-url` | Yes | Submits manual application URL. |
| `POST` | `/api/applications/{session_id}/continue` | Yes | Resumes session after manual action (login/CAPTCHA/questions). |
| `POST` | `/api/applications/{session_id}/stop` | Yes | Terminates active application session & closes browser. |
| `GET` | `/api/applications/{session_id}/browser-status` | Yes | Checks browser instance status (active URL, login wall state). |
| `GET` | `/api/applications/{session_id}/questions` | Yes | Returns unmapped field clarification questions. |
| `POST` | `/api/applications/{session_id}/answers` | Yes | Submits user answers to clarification questions. |
| `GET` | `/api/applications/{session_id}/review` | Yes | Fetches structured review summary grouped by confidence tier. |
| `PATCH` | `/api/applications/{session_id}/fields/{field_id}`| Yes| Overrides value for single form field. |
| `POST` | `/api/applications/{session_id}/validate` | Yes | Re-runs validation checks on form fields. |

#### 6. Settings Router (`/api/settings`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/settings/account` | Yes | Retrieves user account info & metadata. |
| `PATCH` | `/api/settings/account/name` | Yes | Updates display name. |
| `POST` | `/api/settings/account/change-password` | Yes | Changes password after verifying current password. |
| `GET` | `/api/settings/sessions` | Yes | Lists active user refresh token sessions. |
| `DELETE`| `/api/settings/sessions/{session_id}` | Yes | Revokes specific session. |
| `POST` | `/api/settings/sessions/revoke-all` | Yes | Revokes all sessions (sign out everywhere). |
| `GET` | `/api/settings/data-export` | Yes | Downloads complete JSON data export of all user data. |
| `DELETE`| `/api/settings/account` | Yes | Permanently deletes account & cascades all data. |

#### 7. Health & System Router (`/api/health`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/health` | No | Returns system status (`{"status": "ok", "app": "FormPilot AI"}`). |

---

### WebSocket Streaming (`/ws/applications/{session_id}`)

Endpoint: `ws://localhost:8000/ws/applications/{session_id}?token={access_token}`

Real-time agent event stream. Emits structured JSON events:
- `agent_message`: `{ type: "agent_message", node: str, text: str }`
- `jobs_found`: `{ type: "jobs_found", count: int }`
- `fields_extracted`: `{ type: "fields_extracted", count: int }`
- `mapping_complete`: `{ type: "mapping_complete", ready: int, missing: int, ambiguous: int }`
- `manual_action_required`: `{ type: "manual_action_required", reason: str, instructions: str }`
- `review_ready`: `{ type: "review_ready", can_proceed: bool, blocking_issues: list }`
- `ping`: Keepalive ping every 15s.

---

### Local Test Forms

The backend serves HTML test forms in development mode (`APP_ENV=development`) under `http://localhost:8000/test-forms/`:
- `http://localhost:8000/test-forms/simple_form.html`: Standard basic form.
- `http://localhost:8000/test-forms/dynamic_form.html`: Role-type selection dynamically shows/hides conditional fields.
- `http://localhost:8000/test-forms/repeated_sections_form.html`: Dynamic add/remove entry controls for education & experience.
- `http://localhost:8000/test-forms/validation_form.html`: Real-time character counters, pattern checks, password strength meter.
- `http://localhost:8000/test-forms/multi_page_form.html`: Multi-step form navigation.

---

## 🎨 Frontend Documentation

### State Management & API Layer

- **Zustand (`authStore.ts`)**: Persists JWT access/refresh tokens and user state in `localStorage`.
- **Axios Interceptor (`client.ts`)**: Automatically attaches `Bearer <access_token>` to outbound requests. Automatically intercepts `401 Unauthorized` responses and invokes `/api/auth/refresh` to rotate tokens seamlessly.
- **TanStack Query (React Query)**: Handles caching, optimistic updates, and background refetching across pages.

---

### Route Guards & Authentication Flow

Wrapped via `RouteGuards.tsx`:
1. **`RedirectIfAuthed`**: Public routes (`/login`, `/register`, `/forgot-password`). Redirects authenticated users to `/dashboard`.
2. **`RequireAuth`**: Routes requiring valid JWT token (`/verify-email`).
3. **`RequireVerified`**: Routes requiring verified email (`/onboarding`).
4. **`RequireSetup`**: Private routes requiring complete setup (`/dashboard`, `/profile`, `/documents`, `/settings`, `/applications/*`).

---

### Exhaustive Frontend Route Reference

| Path | Component | Auth Level | Description |
|---|---|---|---|
| `/` | `LandingPage.tsx` | Public | Product overview, typewriter demo, features grid, safety promise, CTAs. |
| `/login` | `LoginPage.tsx` | Unauthed | User sign-in with email & password. |
| `/register` | `RegisterPage.tsx` | Unauthed | User account registration. |
| `/verify-email` | `VerifyEmailPage.tsx` | Authed | Email verification pending state & token handler. |
| `/forgot-password` | `ForgotPasswordPage.tsx` | Unauthed | Request password reset link. |
| `/reset-password` | `ResetPasswordPage.tsx` | Public | Set new password via token. |
| `/onboarding` | `OnboardingPage.tsx` | Verified | 10-step initial profile completion wizard. |
| `/dashboard` | `DashboardPage.tsx` | Setup Complete | Prompt box, real-time metrics, active applications table, profile readiness. |
| `/profile` | `ProfilePage.tsx` | Setup Complete | Full profile editor with tabs (Personal, Address, Education, Work, Skills, Projects, Certs, Prefs, Links). |
| `/documents` | `DocumentsPage.tsx` | Setup Complete | Document vault for managing resumes & certificates. |
| `/settings` | `SettingsPage.tsx` | Setup Complete | Account settings, password change, active sessions, data export, account deletion. |
| `/applications` | `HistoryPage.tsx` | Setup Complete | Historical list of all past application sessions with filters. |
| `/applications/start` | `ApplicationsPage.tsx` | Setup Complete | Launch new session via natural language request or direct URL. |
| `/applications/:id/jobs` | `JobResultsPage.tsx` | Setup Complete | View and select from ranked job search results. |
| `/applications/:id/progress` | `ProgressPage.tsx` | Setup Complete | Real-time agent status monitor, live WebSocket logs, pause banners. |
| `/applications/:id/questions` | `QuestionsPage.tsx` | Setup Complete | Clarification interface for unmapped required fields. |
| `/applications/:id/review` | `ReviewPage.tsx` | Setup Complete | Audit table grouped by confidence tier with inline edit & revalidation. |
| `*` | `NotFoundPage` | Public | 404 page with navigation link. |

---

## 🛠️ Local Installation & Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 16 server running locally (or remote connection)

---

### 1. Database Setup
Create a PostgreSQL database named `formpilot`:
```sql
CREATE DATABASE formpilot;
CREATE USER formpilot WITH PASSWORD 'formpilot';
GRANT ALL PRIVILEGES ON DATABASE formpilot TO formpilot;
```

---

### 2. Backend Setup

Navigate to the `backend` directory:
```bash
cd backend
```

Create and activate a Python virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

Configure environment variables by creating `.env` in `backend/`:
```env
APP_NAME="FormPilot AI"
APP_ENV="development"
DEBUG=True
DATABASE_URL="postgresql+asyncpg://formpilot:formpilot@localhost:5432/formpilot"
SECRET_KEY="your-super-secret-key-change-this"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4o-mini"
FRONTEND_URL="http://localhost:5173"
CORS_ORIGINS="http://localhost:5173"
```

Run database migrations:
```bash
alembic upgrade head
```

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Swagger Interactive Docs**: `http://localhost:8000/docs`

---

### 3. Frontend Setup

In a new terminal, navigate to the `frontend` directory:
```bash
cd frontend
```

Install npm dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
- **Frontend Web Application**: `http://localhost:5173`

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more details.
