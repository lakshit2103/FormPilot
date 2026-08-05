import { Loader2 } from 'lucide-react'

export function Spinner({ size = 'md', className = '' }: { className?: string; size?: 'sm' | 'md' | 'lg' }) {
  const pixelSizes = { sm: 16, md: 24, lg: 40 }
  return <Loader2 size={pixelSizes[size] || 24} className={`animate-spin ${className}`} style={{ color: 'var(--brand)' }} />
}

export function PageLoader() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        <Spinner size="lg" />
        <p style={{ fontSize: '14px', color: 'var(--muted)' }}>Loading…</p>
      </div>
    </div>
  )
}

interface ProgressBarProps {
  value: number
  max?: number
  className?: string
  showLabel?: boolean
  color?: 'brand' | 'emerald' | 'amber' | 'rose'
}

export function ProgressBar({ value, max = 100, className = '', showLabel = false }: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }} className={className}>
      <div style={{ flex: 1, height: '8px', backgroundColor: 'var(--line-soft)', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            borderRadius: '4px',
            backgroundColor: 'var(--brand)',
            width: `${pct}%`,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      {showLabel && <span style={{ fontSize: '12px', color: 'var(--muted)', width: '36px', textAlign: 'right' }}>{Math.round(pct)}%</span>}
    </div>
  )
}

interface StepperProps {
  steps: string[]
  currentStep: number
  className?: string
}

export function Stepper({ steps, currentStep, className = '' }: StepperProps) {
  return (
    <div className={`stepper ${className}`.trim()}>
      {steps.map((step, i) => {
        const done = i < currentStep
        const active = i === currentStep
        return (
          <div key={step} className={`step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
            <div className="circ">{done ? '✓' : i + 1}</div>
            <div className="lbl">{step}</div>
          </div>
        )
      })}
    </div>
  )
}
