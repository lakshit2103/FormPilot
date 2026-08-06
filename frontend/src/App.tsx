import { lazy, Suspense } from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/Toast'
import { PageLoader } from '@/components/ui/Loaders'
import {
  RequireAuth, RequireVerified, RequireSetup, RedirectIfAuthed
} from '@/components/auth/RouteGuards'

// Public pages
const LandingPage = lazy(() => import('@/features/landing/LandingPage'))

// Auth pages
const LoginPage = lazy(() => import('@/features/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/features/auth/RegisterPage'))
const VerifyEmailPage = lazy(() => import('@/features/auth/VerifyEmailPage'))
const ForgotPasswordPage = lazy(() => import('@/features/auth/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/features/auth/ResetPasswordPage'))

// App pages
const OnboardingPage = lazy(() => import('@/features/onboarding/OnboardingPage'))
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'))
const ProfilePage = lazy(() => import('@/features/profile/ProfilePage'))
const DocumentsPage = lazy(() => import('@/features/documents/DocumentsPage'))
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage'))
const ApplicationsPage = lazy(() => import('@/features/applications/ApplicationsPage'))

// Application flow pages
const JobResultsPage = lazy(() => import('@/features/applications/JobResultsPage'))
const ProgressPage = lazy(() => import('@/features/applications/ProgressPage'))
const QuestionsPage = lazy(() => import('@/features/applications/QuestionsPage'))
const ReviewPage = lazy(() => import('@/features/applications/ReviewPage'))
const HistoryPage = lazy(() => import('@/features/applications/HistoryPage'))

// 404 page
function NotFoundPage() {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', minHeight: '100vh', gap: 16,
      fontFamily: 'var(--font)', background: 'var(--bg)', color: 'var(--text)',
    }}>
      <div style={{
        fontSize: '4rem', fontWeight: 900,
        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      }}>404</div>
      <h1 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Page Not Found</h1>
      <p style={{ color: 'var(--muted)', fontSize: '0.875rem' }}>
        The page you're looking for doesn't exist.
      </p>
      <a
        href="/"
        style={{
          padding: '10px 24px', background: 'var(--brand)', color: 'white',
          borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: '0.875rem',
        }}
      >
        Go Home
      </a>
    </div>
  )
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60 * 5, retry: 1 },
    mutations: { retry: 0 },
  },
})

const router = createBrowserRouter([
  // ── Public landing page ────────────────────────────────────────────────────
  { path: '/', element: <LandingPage /> },

  // ── Auth pages (redirect if already authenticated) ─────────────────────────
  {
    element: <RedirectIfAuthed />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
    ],
  },

  // ── Requires authentication (email not necessarily verified) ───────────────
  {
    element: <RequireAuth />,
    children: [
      { path: '/verify-email', element: <VerifyEmailPage /> },
    ],
  },

  // ── Requires auth + verified email ─────────────────────────────────────────
  {
    element: <RequireVerified />,
    children: [
      { path: '/onboarding', element: <OnboardingPage /> },
    ],
  },

  // ── Requires full auth + verified + setup complete ─────────────────────────
  {
    element: <RequireSetup />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/profile', element: <ProfilePage /> },
      { path: '/documents', element: <DocumentsPage /> },
      { path: '/settings', element: <SettingsPage /> },

      // Applications — history list
      { path: '/applications', element: <HistoryPage /> },
      // Applications — start new
      { path: '/applications/start', element: <ApplicationsPage /> },

      // Application flow
      { path: '/applications/:sessionId/jobs', element: <JobResultsPage /> },
      { path: '/applications/:sessionId/progress', element: <ProgressPage /> },
      { path: '/applications/:sessionId/questions', element: <QuestionsPage /> },
      { path: '/applications/:sessionId/review', element: <ReviewPage /> },
    ],
  },

  // ── Token-agnostic routes ──────────────────────────────────────────────────
  { path: '/reset-password', element: <ResetPasswordPage /> },

  // ── 404 fallback ───────────────────────────────────────────────────────────
  { path: '*', element: <NotFoundPage /> },
])

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Suspense fallback={<PageLoader />}>
          <RouterProvider router={router} />
        </Suspense>
      </ToastProvider>
    </QueryClientProvider>
  )
}

export default App
