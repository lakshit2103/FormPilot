import { useEffect, useState, createContext, useContext, useCallback } from 'react'
import { X, CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/utils/cn'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

const icons = {
  success: <CheckCircle2 size={16} style={{ color: 'var(--green)' }} />,
  error: <XCircle size={16} style={{ color: 'var(--red)' }} />,
  warning: <AlertTriangle size={16} style={{ color: '#f59e0b' }} />,
  info: <Info size={16} style={{ color: 'var(--brand)' }} />,
}

const borderColors = {
  success: 'var(--green)',
  error: 'var(--red)',
  warning: '#f59e0b',
  info: 'var(--brand)',
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  const remove = useCallback((id: string) => setToasts(prev => prev.filter(t => t.id !== id)), [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        style={{
          position: 'fixed',
          bottom: '16px',
          right: '16px',
          zIndex: 100,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          pointerEvents: 'none',
        }}
        aria-live="polite"
      >
        {toasts.map(t => (
          <div
            key={t.id}
            className="glass-card animate-slide-up"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              padding: '16px',
              pointerEvents: 'auto',
              maxWidth: '400px',
              border: `1px solid ${borderColors[t.type]}`,
              backgroundColor: 'var(--panel-strong)',
            }}
          >
            <div style={{ marginTop: '2px' }}>{icons[t.type]}</div>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text)', flex: 1, lineHeight: 1.4 }}>{t.message}</p>
            <button
              onClick={() => remove(t.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-light)', padding: 0 }}
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)
