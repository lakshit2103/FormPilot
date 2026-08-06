import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, Lock, Eye, EyeOff, Bot } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/components/ui/Toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const { toast } = useToast()
  const [showPw, setShowPw] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const loginMutation = useMutation({
    mutationFn: (data: FormData) => authApi.login(data),
    onSuccess: async (res) => {
      const { access_token, refresh_token, setup_complete } = res.data
      setTokens(access_token, refresh_token)
      // Fetch user info
      const me = await authApi.getMe()
      setUser(me.data)
      toast('Welcome back! 🎉', 'success')
      navigate(setup_complete ? '/dashboard' : '/onboarding', { replace: true })
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Invalid email or password. Please check your credentials or click "Create one" to register.'
      toast(msg, 'error')
    },
  })

  return (
    <div className="page-container">
      <div className="login-card glass-card animate-slide-up">
        {/* Logo */}
        <div className="logo-header">
          <div className="logo-icon">
            <Bot size={28} />
          </div>
          <div>
            <h1 className="logo-title">FormPilot AI</h1>
            <p className="logo-subtitle">AI-Powered Job Applications</p>
          </div>
        </div>

        {/* Card Header */}
        <div>
          <h2 className="auth-title">Welcome back</h2>
          <p className="auth-subtitle">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit(d => loginMutation.mutate(d))} noValidate>
          {/* Email Input Group */}
          <div className="input-group">
            <label htmlFor="login-email" className="input-label">Email address</label>
            <div className="input-wrapper">
              <span className="input-icon-left">
                <Mail size={16} />
              </span>
              <input
                id="login-email"
                type="email"
                className="input-field has-left-icon"
                placeholder="you@example.com"
                autoComplete="email"
                {...register('email')}
              />
            </div>
            {errors.email && <span className="input-error">{errors.email.message}</span>}
          </div>

          {/* Password Input Group */}
          <div className="input-group">
            <label htmlFor="login-password" className="input-label">Password</label>
            <div className="input-wrapper">
              <span className="input-icon-left">
                <Lock size={16} />
              </span>
              <input
                id="login-password"
                type={showPw ? 'text' : 'password'}
                className="input-field has-left-icon has-right-icon"
                placeholder="••••••••"
                autoComplete="current-password"
                {...register('password')}
              />
              <span 
                className="input-icon-right" 
                onClick={() => setShowPw(p => !p)} 
                title={showPw ? "Hide password" : "Show password"}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </span>
            </div>
            {errors.password && <span className="input-error">{errors.password.message}</span>}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
            <Link to="/forgot-password" style={{ fontSize: '13px', fontWeight: 500 }}>
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%' }}
            disabled={loginMutation.isPending}
            id="login-submit"
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account?{' '}
          <Link to="/register" style={{ fontWeight: 600 }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

