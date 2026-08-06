# ⚡ FormPilot AI — Frontend Application Documentation

> **Note**: This file is a mirror of [`frontend/README.md`](./frontend/README.md).

[![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF.svg?logo=vite)](https://vitejs.dev)
[![TanStack Query](https://img.shields.io/badge/TanStack_Query-5.0+-FF4154.svg?logo=reactquery)](https://tanstack.com/query)
[![Zustand](https://img.shields.io/badge/Zustand-4.5+-443E38.svg)](https://zustand-demo.pmnd.rs)

The **FormPilot AI Frontend** is a Single Page Application (SPA) built with **React 19**, **TypeScript**, **Vite**, **TanStack Query (React Query)**, **Zustand**, and a custom **Vanilla CSS Design System**.

---

## 📋 Table of Contents

- [Frontend Architecture](#-frontend-architecture)
- [Directory Structure](#-directory-structure)
- [State Management & Persistence](#-state-management--persistence)
- [HTTP API Client & Automatic Refresh](#-http-api-client--automatic-refresh)
- [Route Guards & Authentication Flow](#-route-guards--authentication-flow)
- [Exhaustive Route Reference](#-exhaustive-route-reference)
- [WebSocket Integration](#-websocket-integration)
- [Design System & CSS Utilities](#-design-system--css-utilities)
- [Setup & Development Commands](#-setup--development-commands)

---

## 📐 Frontend Architecture

```
                               ┌────────────────────────┐
                               │       App.tsx          │
                               │   (React Router v6)    │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
      ┌─────────────▼─────────────┐                 ┌─────────────▼─────────────┐
      │   Public / Unauth Pages   │                 │   Protected App Layout    │
      │ (Landing, Login, Register)│                 │ (Dashboard, Profile, etc.)│
      └───────────────────────────┘                 └─────────────┬─────────────┘
                                                                  │
                                                    ┌─────────────▼─────────────┐
                                                    │  Feature Page Components  │
                                                    └─────────────┬─────────────┘
                                                                  │
                                                    ┌─────────────▼─────────────┐
                                                    │ TanStack Query / Zustand  │
                                                    └─────────────┬─────────────┘
                                                                  │
                                                    ┌─────────────▼─────────────┐
                                                    │ Axios API Client & WS     │
                                                    └───────────────────────────┘
```

---

## 📁 Directory Structure

```
frontend/
├── src/
│   ├── api/                    # Axios API service modules
│   │   ├── applications.ts     # Job application workflow API calls
│   │   ├── auth.ts             # Login, register, email verify, password reset
│   │   ├── client.ts           # Intercepted Axios instance (token refresh)
│   │   ├── documents.ts        # Document vault CRUD API
│   │   ├── profile.ts          # Profile CRUD & completion API
│   │   └── settings.ts         # Account settings, sessions, data export API
│   ├── components/             # Reusable UI components
│   │   ├── auth/               # Route guard wrappers
│   │   │   └── RouteGuards.tsx # RequireAuth, RequireVerified, RequireSetup, RedirectIfAuthed
│   │   ├── layout/             # Layout wrappers
│   │   │   └── AppLayout.tsx   # Topbar + Sidebar shell
│   │   └── ui/                 # Atomic UI component library
│   │       ├── Button.tsx      # Button component with loading state & variants
│   │       ├── Card.tsx        # Panel & Card container
│   │       ├── Input.tsx       # Text & Area Input components
│   │       ├── Loaders.tsx     # ProgressBar & PageLoader components
│   │       └── Toast.tsx       # Toast notification provider & context hook
│   ├── features/               # Feature Page Modules
│   │   ├── applications/       # Job Application Workflow
│   │   │   ├── ApplicationsPage.tsx # Start Application (Natural language / URL)
│   │   │   ├── HistoryPage.tsx      # Past applications history list
│   │   │   ├── JobResultsPage.tsx   # Ranked job search results selection
│   │   │   ├── ProgressPage.tsx     # Real-time WebSocket agent monitor
│   │   │   ├── QuestionsPage.tsx    # Missing field clarification Q&A
│   │   │   └── ReviewPage.tsx       # Confidence-tier review & audit table
│   │   ├── auth/               # Authentication Pages
│   │   │   ├── ForgotPasswordPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── ResetPasswordPage.tsx
│   │   │   └── VerifyEmailPage.tsx
│   │   ├── dashboard/          # Main Dashboard
│   │   │   └── DashboardPage.tsx    # Quick prompt, stats grid, recent sessions
│   │   ├── documents/          # Document Storage
│   │   │   └── DocumentsPage.tsx    # Resume vault & file uploader
│   │   ├── landing/            # Public Product Site
│   │   │   └── LandingPage.tsx      # Landing page with typewriter demo
│   │   ├── onboarding/         # Setup Wizard
│   │   │   └── OnboardingPage.tsx   # 10-step initial profile wizard
│   │   ├── profile/            # Profile Management
│   │   │   └── ProfilePage.tsx      # Profile manager with tabbed sections
│   │   └── settings/           # Account Settings
│   │       └── SettingsPage.tsx     # Password change, sessions, export, delete
│   ├── stores/                 # State Stores (Zustand)
│   │   ├── applicationStore.ts # Active session temporary state
│   │   └── authStore.ts        # Persistent JWT tokens & user info store
│   ├── utils/                  # Helper functions & formatting utilities
│   │   └── cn.ts
│   ├── App.tsx                 # Route definitions & React Query client setup
│   ├── index.css               # Global Design System CSS & variables
│   └── main.tsx                # Entry mount file
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 💾 State Management & Persistence

### 1. `authStore.ts` (Zustand + `localStorage`)
Manages authentication tokens and user account state:
- `user`: Logged-in user object (`id`, `full_name`, `email`, `is_email_verified`, `setup_complete`).
- `accessToken`: Short-lived JWT access token attached to API requests.
- `refreshToken`: Long-lived refresh token stored for silent token rotation.
- `setTokens(access, refresh)`: Updates tokens in state and syncs to `localStorage`.
- `logout()`: Clears all authentication state.

### 2. `applicationStore.ts` (Zustand)
Holds active workflow session state:
- `currentSessionId`: Active `session_id`.
- `jobResults`: Candidate job search results.
- `selectedJob`: Chosen job result.
- `agentMessages`: Live agent event feed.

### 3. TanStack Query (React Query)
Handles caching, revalidation, and loading states for API endpoints:
- `staleTime: 5 minutes` by default.
- Queries automatically refetch on window focus or mutation invalidation.

---

## 🔒 HTTP API Client & Automatic Refresh

The central Axios client (`src/api/client.ts`) handles API communication:

1. **Request Interceptor**:
   Reads `accessToken` from `authStore.ts` and sets header:
   `Authorization: Bearer <access_token>`

2. **Response Interceptor (401 Handling)**:
   If an API call returns `401 Unauthorized`:
   - Pauses queued requests.
   - Makes a `POST /api/auth/refresh` call using the stored `refreshToken`.
   - On success, updates tokens in `authStore.ts` and retries failed requests.
   - On failure, clears auth state (`logout()`) and redirects to `/login`.

---

## 🛡️ Route Guards & Authentication Flow

Page accessibility is governed by higher-order Route Guard wrappers in `src/components/auth/RouteGuards.tsx`:

- **`RedirectIfAuthed`**: Wraps unauthenticated pages (`/login`, `/register`, `/forgot-password`). If the user is logged in, automatically redirects to `/dashboard`.
- **`RequireAuth`**: Ensures a user has logged in (`/verify-email`).
- **`RequireVerified`**: Ensures the user has verified their email address (`/onboarding`).
- **`RequireSetup`**: Ensures full authentication, email verification, and onboarding completion (`/dashboard`, `/profile`, `/documents`, `/settings`, `/applications/*`).

---

## 🗺️ Exhaustive Route Reference

| Path | Component | Guard Level | Purpose |
|---|---|---|---|
| `/` | `LandingPage.tsx` | Public | Landing page with typewriter tagline, feature grid, safety promise, and CTAs. |
| `/login` | `LoginPage.tsx` | Unauthenticated | User login form. |
| `/register` | `RegisterPage.tsx` | Unauthenticated | User registration form. |
| `/verify-email` | `VerifyEmailPage.tsx` | Authenticated | Email verification status view. |
| `/forgot-password` | `ForgotPasswordPage.tsx` | Unauthenticated | Request password reset token. |
| `/reset-password` | `ResetPasswordPage.tsx` | Public | Set new password via token link. |
| `/onboarding` | `OnboardingPage.tsx` | Email Verified | 10-step setup wizard for initial profile building. |
| `/dashboard` | `DashboardPage.tsx` | Setup Complete | Main dashboard with prompt input, real stats, recent activity table. |
| `/profile` | `ProfilePage.tsx` | Setup Complete | Full profile manager tabs (Personal, Education, Work, Skills, Projects, etc.). |
| `/documents` | `DocumentsPage.tsx` | Setup Complete | Document vault for uploading and managing resumes & certificates. |
| `/settings` | `SettingsPage.tsx` | Setup Complete | Account settings, password change, active sessions, data export, delete account. |
| `/applications` | `HistoryPage.tsx` | Setup Complete | History list of all past application sessions. |
| `/applications/start` | `ApplicationsPage.tsx` | Setup Complete | Launch session via Natural Language request or Direct URL. |
| `/applications/:sessionId/jobs` | `JobResultsPage.tsx` | Setup Complete | Browse and select from ranked job search results. |
| `/applications/:sessionId/progress` | `ProgressPage.tsx` | Setup Complete | Real-time agent status monitor with live WebSocket logs and pause banners. |
| `/applications/:sessionId/questions` | `QuestionsPage.tsx` | Setup Complete | Clarification Q&A view for unmapped required fields. |
| `/applications/:sessionId/review` | `ReviewPage.tsx` | Setup Complete | Review mapping audit table grouped by confidence tier with inline edit. |
| `*` | `NotFoundPage` | Public | Styled 404 page with navigation link. |

---

## 📡 WebSocket Integration

The `ProgressPage.tsx` establishes a WebSocket connection to stream real-time agent updates:

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/applications/${sessionId}?token=${accessToken}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'agent_message') {
    // Append to message feed
  } else if (data.type === 'manual_action_required') {
    // Show pause banner for login/CAPTCHA/questions
  } else if (data.type === 'review_ready') {
    // Navigate to review page
  }
};
```

---

## 🎨 Design System & CSS Utilities

FormPilot AI uses a clean Vanilla CSS design system (`src/index.css`):

### CSS Variables
- `--bg`: `#0a0a0e` (Dark background)
- `--panel`: `#12121a` (Card background)
- `--panel-strong`: `#181824` (Input/Strong card background)
- `--brand`: `#6366f1` (Indigo primary brand)
- `--brand-light`: `rgba(99, 102, 241, 0.15)`
- `--green`: `#22c55e` (Success indicator)
- `--amber`: `#f59e0b` (Warning/Review indicator)
- `--red`: `#ef4444` (Error/Danger indicator)
- `--text`: `#f1f5f9` (Primary text)
- `--muted`: `#94a3b8` (Secondary text)
- `--line`: `#27273a` (Borders and dividers)

---

## 🛠️ Setup & Development Commands

### 1. Requirements
- Node.js 18+
- npm 9+

### 2. Environment Configuration (`frontend/.env`)
```env
VITE_API_URL="http://localhost:8000"
```

### 3. Installation & Run Commands

```bash
cd frontend

# Install dependencies
npm install

# Start development server with HMR
npm run dev

# Run TypeScript type check
npx tsc --noEmit

# Build production bundle
npm run build
```
