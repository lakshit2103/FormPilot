import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, CheckCircle2, Bot } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/auth'
import { useToast } from '@/components/ui/Toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

const schema = z.object({ email: z.string().email('Enter a valid email') })
type FormData = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const { toast } = useToast()
  const [sent, setSent] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => authApi.forgotPassword(data.email),
    onSuccess: () => setSent(true),
    onError: () => toast('Something went wrong. Please try again.', 'error'),
  })

  if (sent) {
    return (
      <div className="page-container">
        <div className="glass-card login-card animate-slide-up" style={{ textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(47, 111, 79, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', color: 'var(--green)' }}>
            <CheckCircle2 size={32} />
          </div>
          <h2 className="auth-title">Check your email</h2>
          <p className="auth-subtitle">
            If an account exists with that email, we've sent a password reset link. It expires in 1 hour.
          </p>
          <Link to="/login">
            <Button variant="ghost" style={{ width: '100%' }}>Back to Sign in</Button>
          </Link>
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
            <h2 className="auth-title">Forgot your password?</h2>
            <p className="auth-subtitle" style={{ marginBottom: 0 }}>Enter your email and we'll send a reset link.</p>
          </div>
          <form onSubmit={handleSubmit(d => mutation.mutate(d))} noValidate>
            <Input
              label="Email address"
              type="email"
              id="forgot-email"
              placeholder="you@example.com"
              leftIcon={<Mail size={16} />}
              error={errors.email?.message}
              required
              {...register('email')}
            />
            <Button type="submit" style={{ width: '100%', marginTop: '16px' }} size="lg" isLoading={mutation.isPending} id="forgot-submit">
              Send reset link
            </Button>
          </form>
          <div className="auth-footer">
            <Link to="/login">Back to Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
