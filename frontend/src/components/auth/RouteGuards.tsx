import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { PageLoader } from '@/components/ui/Loaders'

export function RequireAuth() {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Outlet />
}

export function RequireVerified() {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!user?.is_email_verified) return <Navigate to="/verify-email" replace />
  return <Outlet />
}

export function RequireSetup() {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!user?.is_email_verified) return <Navigate to="/verify-email" replace />
  return <Outlet />
}

export function RedirectIfAuthed() {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Outlet />
  if (!user?.is_email_verified) return <Navigate to="/verify-email" replace />
  return <Navigate to="/dashboard" replace />
}
