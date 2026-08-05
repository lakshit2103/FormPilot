import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'brand' | 'ghost' | 'danger' | 'outline' | 'primary'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const variantMap: Record<string, string> = {
  brand: 'btn-brand',
  primary: 'btn-primary',
  ghost: 'btn-ghost',
  danger: 'btn-danger',
  outline: 'btn-outline',
}

const sizePaddingMap: Record<string, React.CSSProperties> = {
  sm: { padding: '6px 12px', fontSize: '12px' },
  md: { padding: '10px 20px', fontSize: '14px' },
  lg: { padding: '12px 28px', fontSize: '16px' },
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'brand', size = 'md', isLoading, leftIcon, rightIcon, children, disabled, style, ...props }, ref) => {
    const btnClass = `${variantMap[variant] || 'btn-brand'} ${className}`.trim()
    const sizeStyle = sizePaddingMap[size] || {}

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={btnClass}
        style={{ ...sizeStyle, ...style }}
        {...props}
      >
        {isLoading ? <Loader2 size={16} className="animate-spin" /> : leftIcon}
        {children}
        {!isLoading && rightIcon}
      </button>
    )
  }
)
Button.displayName = 'Button'
