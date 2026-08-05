interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  style?: React.CSSProperties
}

const paddingMap: Record<string, string> = {
  none: '0',
  sm: '16px',
  md: '24px',
  lg: '32px',
}

export function Card({ children, className = '', hover = false, padding = 'md', style, ...props }: CardProps) {
  const cardClass = `${hover ? 'glass-card-hover' : 'glass-card'} ${className}`.trim()
  const pad = paddingMap[padding] || '24px'

  return (
    <div
      className={cardClass}
      style={{ padding: pad, ...style }}
      {...props}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  icon?: React.ReactNode
}

export function CardHeader({ title, subtitle, action, icon }: CardHeaderProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {icon && (
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: 'var(--brand-light)',
            border: '1px solid var(--line)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--brand)'
          }}>
            {icon}
          </div>
        )}
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>{title}</h3>
          {subtitle && <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>{subtitle}</p>}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
