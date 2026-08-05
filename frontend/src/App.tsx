import { lazy, Suspense } from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/Toast'
import { PageLoader } from '@/components/ui/Loaders'
import {
  RequireAuth, RequireVerified, RequireSetup, RedirectIfAuthed
} from '@/components/auth/RouteGuards'

// Lazy loaded pages
const LoginPage = lazy(() => import('@/features/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/features/auth/RegisterPage'))
const VerifyEmailPage = lazy(() => import('@/features/auth/VerifyEmailPage'))
const ForgotPasswordPage = lazy(() => import('@/features/auth/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/features/auth/ResetPasswordPage'))
const OnboardingPage = lazy(() => import('@/features/onboarding/OnboardingPage'))
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'))
const ProfilePage = lazy(() => import('@/features/profile/ProfilePage'))
const DocumentsPage = lazy(() => import('@/features/documents/DocumentsPage'))
const ApplicationsPage = lazy(() => import('@/features/applications/ApplicationsPage'))

// Application flow pages
const JobResultsPage = lazy(() => import('@/features/applications/JobResultsPage'))
const ProgressPage = lazy(() => import('@/features/applications/ProgressPage'))
const QuestionsPage = lazy(() => import('@/features/applications/QuestionsPage'))
const ReviewPage = lazy(() => import('@/features/applications/ReviewPage'))
const HistoryPage = lazy(() => import('@/features/applications/HistoryPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60 * 5, retry: 1 },
    mutations: { retry: 0 },
  },
})

const router = createBrowserRouter([
  // Public — redirect to app if already authed
  {
    element: <RedirectIfAuthed />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
    ],
  },
  // Requires auth (but not verified)
  {
    element: <RequireAuth />,
    children: [
      { path: '/verify-email', element: <VerifyEmailPage /> },
    ],
  },
  // Requires auth + verified email but not necessarily setup
  {
    element: <RequireVerified />,
    children: [
      { path: '/onboarding', element: <OnboardingPage /> },
    ],
  },
  // Requires full auth + verified + setup complete
  {
    element: <RequireSetup />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/profile', element: <ProfilePage /> },
      { path: '/documents', element: <DocumentsPage /> },
      { path: '/applications', element: <HistoryPage /> },
      { path: '/applications/start', element: <ApplicationsPage /> },

      // Application flow
      { path: '/applications/:sessionId/jobs', element: <JobResultsPage /> },
      { path: '/applications/:sessionId/progress', element: <ProgressPage /> },
      { path: '/applications/:sessionId/questions', element: <QuestionsPage /> },
      { path: '/applications/:sessionId/review', element: <ReviewPage /> },
    ],
  },
  // Catch-all redirect handled by token state
  { path: '/reset-password', element: <ResetPasswordPage /> },
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '*', element: <div className="page-container">Page not found</div> },
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
