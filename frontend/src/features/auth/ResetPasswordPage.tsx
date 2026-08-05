import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Lock, Eye, EyeOff, CheckCircle2, Bot } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/auth'
import { useToast } from '@/components/ui/Toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

const schema = z.object({
  new_password: z.string()
    .min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[0-9]/, 'Must contain a number'),
  confirm: z.string(),
}).refine(d => d.new_password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })

type FormData = z.infer<typeof schema>

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [showPw, setShowPw] = useState(false)
  const [done, setDone] = useState(false)
  const token = searchParams.get('token') || ''

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => authApi.resetPassword(token, data.new_password),
    onSuccess: () => setDone(true),
    onError: (err: any) => toast(err?.response?.data?.detail || 'Reset failed.', 'error'),
  })

  if (!token) {
    return (
      <div className="page-container">
        <div className="glass-card login-card text-center" style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--muted)', fontSize: '14px' }}>Invalid or missing reset token.</p>
          <Link to="/forgot-password" style={{ color: 'var(--brand)', marginTop: '16px', display: 'inline-block' }}>Request a new link</Link>
        </div>
      </div>
    )
  }

  if (done) {
    return (
      <div className="page-container">
        <div className="glass-card login-card animate-slide-up" style={{ textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(47, 111, 79, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', color: 'var(--green)' }}>
            <CheckCircle2 size={32} />
          </div>
          <h2 className="auth-title">Password updated!</h2>
          <p className="auth-subtitle">Your password has been reset. You can now sign in.</p>
          <Button style={{ width: '100%' }} onClick={() => navigate('/login')}>Sign in</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="login-card animate-slide-up">
        <div className="logo-header">
          <div className="logo-icon">
            <Bot size={24} />
          </div>
          <div>
            <div className="logo-title">FormPilot AI</div>
            <div className="logo-subtitle">AI-Powered Job Applications</div>
          </div>
        </div>
        <div className="glass-card" style={{ padding: '32px' }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 className="auth-title">Set a new password</h2>
            <p className="auth-subtitle" style={{ marginBottom: 0 }}>Choose a strong password for your account.</p>
          </div>
          <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
            <Input
              label="New password"
              type={showPw ? 'text' : 'password'}
              id="reset-password"
              placeholder="Min 8 chars, 1 uppercase, 1 number"
              leftIcon={<Lock size={16} />}
              rightIcon={
                <button type="button" onClick={() => setShowPw(p => !p)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              }
              error={errors.new_password?.message}
              required
              {...register('new_password')}
            />
            <Input
              label="Confirm password"
              type={showPw ? 'text' : 'password'}
              id="reset-confirm"
              placeholder="Repeat your password"
              leftIcon={<Lock size={16} />}
              error={errors.confirm?.message}
              required
              {...register('confirm')}
            />
            <Button type="submit" style={{ width: '100%', marginTop: '16px' }} size="lg" isLoading={mutation.isPending} id="reset-submit">
              Reset password
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
