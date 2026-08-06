import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Zap, Link2, ArrowRight, Sparkles } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { applicationsApi } from '@/api/applications'
import { useToast } from '@/components/ui/Toast'

type Mode = 'natural' | 'url'

const EXAMPLES = [
  'Find and fill the TCS application for an Agentic AI Engineer role',
  'Apply for a remote Python internship in Bangalore',
  'Search for ML Engineer roles at Infosys and fill the form',
  'Find a Data Science internship and complete the application',
]

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { addToast } = useToast()

  const [mode, setMode] = useState<Mode>('natural')
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [url, setUrl] = useState('')

  // Create session + trigger search
  const startMut = useMutation({
    mutationFn: async () => {
      if (mode === 'natural') {
        if (!query.trim()) throw new Error('Please enter a job search request.')
        // 1. Create session
        const session = await applicationsApi.start({ user_query: query.trim() })
        // 2. Trigger search phase
        await applicationsApi.triggerSearch(session.id)
        return session
      } else {
        if (!url.trim()) throw new Error('Please enter a valid URL.')
        // For direct URL: create session with a synthetic query
        const session = await applicationsApi.start({
          user_query: `Open and fill: ${url.trim()}`,
        })
        // 3. Provide URL directly — skips search
        await applicationsApi.provideUrl(session.id, url.trim())
        return session
      }
    },
    onSuccess: (session) => {
      if (mode === 'natural') {
        // Navigate to job results page where user picks from search results
        navigate(`/applications/${session.id}/jobs`)
      } else {
        // Navigate to progress page (direct URL — goes straight to navigation + fill)
        navigate(`/applications/${session.id}/progress`)
      }
    },
    onError: (err: any) => {
      addToast(err?.message || err?.response?.data?.detail || 'Failed to start application', 'error')
    },
  })

  const handleStart = () => {
    startMut.mutate()
  }

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>

        {/* Header */}
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Start an Application</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginTop: 4 }}>
            Describe what you're looking for, or paste a form URL directly.
          </p>
        </div>

        {/* Mode switcher */}
        <div style={{
          display: 'inline-flex', background: 'var(--panel)', border: '1px solid var(--line)',
          borderRadius: 10, padding: 4, width: 'fit-content', gap: 4,
        }}>
          {(['natural', 'url'] as Mode[]).map(m => (
            <button
              key={m}
              id={`mode-${m}`}
              onClick={() => setMode(m)}
              style={{
                padding: '8px 18px', border: 'none', borderRadius: 8,
                cursor: 'pointer', fontSize: '0.875rem', fontWeight: 500,
                background: mode === m ? 'var(--brand)' : 'transparent',
                color: mode === m ? 'white' : 'var(--muted)',
                transition: 'all 0.2s',
              }}
            >
              {m === 'natural' ? (
                <><Sparkles size={13} style={{ display: 'inline', marginRight: 6 }} />Natural Language</>
              ) : (
                <><Link2 size={13} style={{ display: 'inline', marginRight: 6 }} />Direct URL</>
              )}
            </button>
          ))}
        </div>

        {/* Input card */}
        <Card style={{ background: 'var(--panel-strong)' }}>
          {mode === 'natural' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label
                  htmlFor="app-query"
                  style={{ fontSize: '0.875rem', fontWeight: 600, display: 'block', marginBottom: 8 }}
                >
                  What role are you applying for?
                </label>
                <textarea
                  id="app-query"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleStart() }}
                  placeholder='e.g. "Find and fill the TCS Agentic AI Engineer application form"'
                  rows={3}
                  style={{
                    width: '100%', padding: '12px 16px',
                    border: '1px solid var(--line)', borderRadius: 10,
                    background: 'var(--bg)', color: 'var(--text)',
                    fontSize: '0.9rem', resize: 'none', outline: 'none',
                    fontFamily: 'inherit', lineHeight: 1.5,
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={e => { e.target.style.borderColor = 'var(--brand)' }}
                  onBlur={e => { e.target.style.borderColor = 'var(--line)' }}
                />
                <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 6 }}>
                  Press Ctrl+Enter to start · FormPilot will search for the correct form page.
                </p>
              </div>

              {/* Example chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {EXAMPLES.map(ex => (
                  <button
                    key={ex}
                    onClick={() => setQuery(ex)}
                    style={{
                      background: 'none', border: '1px solid var(--line)',
                      borderRadius: 6, padding: '4px 10px', fontSize: '0.75rem',
                      color: 'var(--muted)', cursor: 'pointer', transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { (e.target as HTMLElement).style.borderColor = 'var(--brand)'; (e.target as HTMLElement).style.color = 'var(--brand)' }}
                    onMouseLeave={e => { (e.target as HTMLElement).style.borderColor = 'var(--line)'; (e.target as HTMLElement).style.color = 'var(--muted)' }}
                  >
                    {ex.length > 48 ? ex.slice(0, 48) + '…' : ex}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label
                  htmlFor="app-url"
                  style={{ fontSize: '0.875rem', fontWeight: 600, display: 'block', marginBottom: 8 }}
                >
                  Form / Application URL
                </label>
                <input
                  id="app-url"
                  type="url"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleStart()}
                  placeholder="https://boards.greenhouse.io/company/jobs/12345"
                  className="input-field"
                  style={{ fontSize: '0.9rem' }}
                />
                <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 6 }}>
                  FormPilot will open this page, extract all fields and fill them using your profile.
                  You will need to log in manually if required.
                </p>
              </div>
            </div>
          )}

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              id="start-application-btn"
              leftIcon={mode === 'natural' ? <Zap size={16} /> : <ArrowRight size={16} />}
              isLoading={startMut.isPending}
              disabled={mode === 'natural' ? !query.trim() : !url.trim()}
              onClick={handleStart}
              style={{ minWidth: 160 }}
            >
              {startMut.isPending
                ? (mode === 'natural' ? 'Searching…' : 'Opening…')
                : (mode === 'natural' ? 'Search & Fill' : 'Open & Fill')}
            </Button>
          </div>
        </Card>

        {/* What happens next */}
        <Card>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--muted)', marginBottom: 16 }}>
            WHAT HAPPENS NEXT
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            {(mode === 'natural' ? [
              { step: '1', title: 'Search', desc: 'FormPilot queries DuckDuckGo and finds candidate pages.' },
              { step: '2', title: 'You Select', desc: 'Pick the correct result from ranked options.' },
              { step: '3', title: 'Extract & Map', desc: 'Fields are extracted and matched to your profile.' },
              { step: '4', title: 'Review & Fill', desc: 'You review everything before any action.' },
            ] : [
              { step: '1', title: 'Open Page', desc: 'Playwright navigates to the URL you provided.' },
              { step: '2', title: 'Login if Needed', desc: 'FormPilot pauses; you log in manually.' },
              { step: '3', title: 'Extract & Map', desc: 'Fields are extracted and matched to your profile.' },
              { step: '4', title: 'Review & Fill', desc: 'You review everything before any action.' },
            ]).map(({ step, title, desc }) => (
              <div key={step} style={{ display: 'flex', gap: 12 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand)',
                }}>{step}</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: 2 }}>{title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.4 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>

      </div>
    </AppLayout>
  )
}
