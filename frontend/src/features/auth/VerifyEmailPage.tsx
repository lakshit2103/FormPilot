import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle2, XCircle, Loader2, Mail } from 'lucide-react'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/components/ui/Toast'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setUser, user } = useAuthStore()
  const { toast } = useToast()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')

  const verifyMutation = useMutation({
    mutationFn: (t: string) => authApi.verifyEmail(t),
    onSuccess: (res) => { setUser(res.data); setStatus('success') },
    onError: () => setStatus('error'),
  })

  const resendMutation = useMutation({
    mutationFn: () => authApi.resendVerification(user?.email || ''),
    onSuccess: () => toast('Verification email resent!', 'success'),
    onError: () => toast('Failed to resend. Please try again.', 'error'),
  })

  useEffect(() => {
    if (token && status === 'idle') {
      setStatus('loading')
      verifyMutation.mutate(token)
    }
  }, [token])

  if (status === 'loading') {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center' }}>
          <Loader2 size={40} style={{ animation: 'spin 1s linear infinite', color: 'var(--brand)', margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--muted)' }}>Verifying your email…</p>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="page-container">
        <div className="glass-card login-card animate-slide-up" style={{ textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(47, 111, 79, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', color: 'var(--green)' }}>
            <CheckCircle2 size={32} />
          </div>
          <h2 className="auth-title">Email verified!</h2>
          <p className="auth-subtitle">Your account is now active. Let's set up your profile.</p>
          <Button style={{ width: '100%' }} onClick={() => navigate('/onboarding')}>
            Set up my profile
          </Button>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="page-container">
        <div className="glass-card login-card animate-slide-up" style={{ textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(152, 75, 78, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', color: 'var(--rose)' }}>
            <XCircle size={32} />
          </div>
          <h2 className="auth-title">Link expired</h2>
          <p className="auth-subtitle">This verification link has expired or already been used.</p>
          {user && (
            <Button style={{ width: '100%', marginBottom: '12px' }} onClick={() => resendMutation.mutate()} isLoading={resendMutation.isPending}>
              Resend verification email
            </Button>
          )}
          <Button variant="ghost" style={{ width: '100%' }} onClick={() => navigate('/login')}>Back to Sign in</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="glass-card login-card animate-slide-up" style={{ textAlign: 'center' }}>
        <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'var(--brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', color: 'var(--brand)' }}>
          <Mail size={32} />
        </div>
        <h2 className="auth-title">Check your inbox</h2>
        <p className="auth-subtitle">
          We sent a verification link to <strong style={{ color: 'var(--text)' }}>{user?.email}</strong>. Click it to activate your account.
        </p>
        {user && (
          <Button variant="outline" style={{ width: '100%', marginBottom: '12px' }} onClick={() => resendMutation.mutate()} isLoading={resendMutation.isPending}>
            Resend email
          </Button>
        )}
        <div className="auth-footer">
          <Link to="/login">Back to Sign in</Link>
        </div>
      </div>
    </div>
  )
}
