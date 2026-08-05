import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { User, Mail, Lock, Eye, EyeOff, Bot } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/auth'
import { useToast } from '@/components/ui/Toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

const schema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[0-9]/, 'Must contain a number'),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })

type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [showPw, setShowPw] = useState(false)
  const [registered, setRegistered] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const registerMutation = useMutation({
    mutationFn: (data: FormData) => authApi.register({ full_name: data.full_name, email: data.email, password: data.password }),
    onSuccess: () => setRegistered(true),
    onError: (err: any) => {
      toast(err?.response?.data?.detail || 'Registration failed.', 'error')
    },
  })

  if (registered) {
    return (
      <div className="page-container">
        <div className="login-card glass-card animate-slide-up" style={{ textAlign: 'center' }}>
          <div style={{ margin: '0 auto 20px', width: '64px', height: '64px', backgroundColor: 'var(--green)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
            <Mail size={32} />
          </div>
          <h2 className="auth-title">Check your inbox!</h2>
          <p className="auth-subtitle" style={{ marginBottom: '24px' }}>
            We've sent a verification link to your email. Click it to activate your account.
          </p>
          <button onClick={() => navigate('/login')} className="btn-primary" style={{ width: '100%', backgroundColor: 'transparent', color: 'var(--brand)', border: '1px solid var(--brand)' }}>
            Back to Sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="login-card glass-card animate-slide-up">
        <div className="logo-header">
          <div className="logo-icon">
            <Bot size={28} />
          </div>
          <div>
            <h1 className="logo-title">FormPilot AI</h1>
            <p className="logo-subtitle">AI-Powered Job Applications</p>
          </div>
        </div>

        <div>
          <h2 className="auth-title">Create your account</h2>
          <p className="auth-subtitle">Start automating your job applications</p>
        </div>

        <form onSubmit={handleSubmit(d => registerMutation.mutate(d))} noValidate>
          <div className="input-group">
            <label htmlFor="register-name" className="input-label">Full name</label>
            <div className="input-wrapper">
              <span className="input-icon-left"><User size={16} /></span>
              <input
                id="register-name"
                type="text"
                className="input-field has-left-icon"
                placeholder="Lakshit Sehdev"
                autoComplete="name"
                required
                {...register('full_name')}
              />
            </div>
            {errors.full_name && <span className="input-error">{errors.full_name.message}</span>}
          </div>

          <div className="input-group">
            <label htmlFor="register-email" className="input-label">Email address</label>
            <div className="input-wrapper">
              <span className="input-icon-left"><Mail size={16} /></span>
              <input
                id="register-email"
                type="email"
                className="input-field has-left-icon"
                placeholder="you@example.com"
                autoComplete="email"
                required
                {...register('email')}
              />
            </div>
            {errors.email && <span className="input-error">{errors.email.message}</span>}
          </div>

          <div className="input-group">
            <label htmlFor="register-password" className="input-label">Password</label>
            <div className="input-wrapper">
              <span className="input-icon-left"><Lock size={16} /></span>
              <input
                id="register-password"
                type={showPw ? 'text' : 'password'}
                className="input-field has-left-icon has-right-icon"
                placeholder="Min 8 chars, 1 uppercase, 1 number"
                autoComplete="new-password"
                required
                {...register('password')}
              />
              <span className="input-icon-right" onClick={() => setShowPw(p => !p)}>
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </span>
            </div>
            {errors.password && <span className="input-error">{errors.password.message}</span>}
          </div>

          <div className="input-group" style={{ marginBottom: '24px' }}>
            <label htmlFor="register-confirm" className="input-label">Confirm password</label>
            <div className="input-wrapper">
              <span className="input-icon-left"><Lock size={16} /></span>
              <input
                id="register-confirm"
                type={showPw ? 'text' : 'password'}
                className="input-field has-left-icon"
                placeholder="Repeat your password"
                autoComplete="new-password"
                required
                {...register('confirm')}
              />
            </div>
            {errors.confirm && <span className="input-error">{errors.confirm.message}</span>}
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%' }} disabled={registerMutation.isPending} id="register-submit">
            {registerMutation.isPending ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{' '}
          <Link to="/login" style={{ fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
