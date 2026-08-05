import { forwardRef } from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, hint, leftIcon, rightIcon, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const hasLeft = Boolean(leftIcon)
    const hasRight = Boolean(rightIcon)

    return (
      <div className="input-group">
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
            {props.required && <span style={{ color: 'var(--rose)', marginLeft: '4px' }}>*</span>}
          </label>
        )}
        <div className="input-wrapper">
          {leftIcon && <span className="input-icon-left">{leftIcon}</span>}
          <input
            ref={ref}
            id={inputId}
            className={`input-field ${hasLeft ? 'has-left-icon' : ''} ${hasRight ? 'has-right-icon' : ''} ${className}`.trim()}
            style={error ? { borderColor: 'var(--rose)' } : undefined}
            {...props}
          />
          {rightIcon && <span className="input-icon-right">{rightIcon}</span>}
        </div>
        {error && <span className="input-error">{error}</span>}
        {hint && !error && <span style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>{hint}</span>}
      </div>
    )
  }
)
Input.displayName = 'Input'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', label, error, hint, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="input-group">
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
            {props.required && <span style={{ color: 'var(--rose)', marginLeft: '4px' }}>*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          rows={4}
          className={`input-field ${className}`.trim()}
          style={{ resize: 'none', ...(error ? { borderColor: 'var(--rose)' } : {}) }}
          {...props}
        />
        {error && <span className="input-error">{error}</span>}
        {hint && !error && <span style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>{hint}</span>}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'
