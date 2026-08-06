import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Zap, History, FileText, TrendingUp, Clock, CheckCircle2,
  AlertCircle, Play
} from 'lucide-react'
import { profileApi } from '@/api/profile'
import { applicationsApi } from '@/api/applications'
import { useAuthStore } from '@/stores/authStore'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ProgressBar } from '@/components/ui/Loaders'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  created:    { label: 'Created',    className: 'tag tag-muted' },
  searching:  { label: 'Searching',  className: 'tag tag-info' },
  navigating: { label: 'Navigating', className: 'tag tag-info' },
  running:    { label: 'Running',    className: 'tag tag-info' },
  paused:     { label: 'Paused',     className: 'tag tag-warning' },
  reviewing:  { label: 'In Review',  className: 'tag tag-warning' },
  completed:  { label: 'Completed',  className: 'tag tag-success' },
  failed:     { label: 'Failed',     className: 'tag tag-error' },
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const { data: completionData } = useQuery({
    queryKey: ['profile-completion'],
    queryFn: () => profileApi.getCompletion().then(r => r.data),
  })

  const { data: sessions = [] } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(),
  })

  const { data: documents = [] } = useQuery({
    queryKey: ['documents-count'],
    queryFn: async () => {
      const { apiClient } = await import('@/api/client')
      const r = await apiClient.get('/api/documents')
      return r.data
    },
  })

  const overall = completionData?.overall_percentage ?? 0

  // Derived stats from real data
  const totalSessions = sessions.length
  const completedSessions = sessions.filter((s: any) => s.status === 'completed').length
  const pausedSessions = sessions.filter((s: any) => s.status === 'paused' || s.status === 'reviewing').length
  const totalDocs = Array.isArray(documents) ? documents.length : 0

  const handleStart = () => {
    if (query.trim()) {
      navigate(`/applications/start?q=${encodeURIComponent(query.trim())}`)
    } else {
      navigate('/applications/start')
    }
  }

  const recentSessions = [...sessions].slice(0, 5)

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

        {/* Welcome */}
        {user && (
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700 }}>
              Welcome back, {user.full_name?.split(' ')[0] || 'there'} 👋
            </h1>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginTop: 4 }}>
              What role would you like to apply for today?
            </p>
          </div>
        )}

        {/* Natural-language command box */}
        <Card style={{ backgroundColor: 'var(--panel-strong)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <input
              id="dashboard-query"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleStart()}
              placeholder='e.g. "Find and fill the TCS application for an Agentic AI Engineer role"'
              className="input-field"
              style={{ flex: 1, padding: '12px 16px', fontSize: '14px' }}
              aria-label="Job search query"
            />
            <Button
              id="dashboard-start"
              onClick={handleStart}
              leftIcon={<Zap size={16} />}
            >
              Start
            </Button>
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
            {['TCS Agentic AI Engineer', 'Remote Python Internship', 'ML Engineer Bangalore'].map(s => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                style={{
                  background: 'none', border: '1px solid var(--line)', borderRadius: '4px',
                  padding: '4px 10px', fontSize: '12px', color: 'var(--muted)', cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { (e.target as HTMLElement).style.borderColor = 'var(--brand)'; (e.target as HTMLElement).style.color = 'var(--brand)' }}
                onMouseLeave={e => { (e.target as HTMLElement).style.borderColor = 'var(--line)'; (e.target as HTMLElement).style.color = 'var(--muted)' }}
              >
                {s}
              </button>
            ))}
          </div>
        </Card>

        {/* Stats grid — real data */}
        <div className="grid-4">
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <TrendingUp size={12} /> Applications
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--brand)' }}>{totalSessions}</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 size={12} /> Completed
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--green)' }}>{completedSessions}</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertCircle size={12} /> Profile
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--brand)' }}>{Math.round(overall)}%</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileText size={12} /> Documents
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--amber)' }}>{totalDocs}</div>
          </Card>
        </div>

        {/* Recent Applications — real data */}
        <div>
          <div className="section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Recent Applications</span>
            <Button variant="ghost" size="sm" onClick={() => navigate('/applications')}>View all</Button>
          </div>
          {recentSessions.length === 0 ? (
            <Card style={{ textAlign: 'center', padding: '40px 24px' }}>
              <History size={32} color="var(--muted)" style={{ margin: '0 auto 12px', display: 'block' }} />
              <p style={{ color: 'var(--muted)', fontSize: '0.875rem' }}>No applications yet. Start one above!</p>
            </Card>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Company</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.map((s: any) => {
                  const cfg = STATUS_CONFIG[s.status] || { label: s.status, className: 'tag' }
                  const updated = s.updated_at ? new Date(s.updated_at) : null
                  const isPaused = ['paused', 'reviewing'].includes(s.status)
                  return (
                    <tr key={s.id}>
                      <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {s.role || s.user_query?.slice(0, 40) || '—'}
                      </td>
                      <td>{s.company || '—'}</td>
                      <td><span className={cfg.className}>{cfg.label}</span></td>
                      <td style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>
                        {updated ? updated.toLocaleDateString() : '—'}
                      </td>
                      <td>
                        <Button
                          variant={isPaused ? 'primary' : 'outline'}
                          size="sm"
                          leftIcon={isPaused ? <Play size={12} /> : undefined}
                          onClick={() => navigate(`/applications/${s.id}/${isPaused ? 'progress' : 'review'}`)}
                        >
                          {isPaused ? 'Resume' : 'View'}
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Profile Completion */}
        <div className="section-title">Profile Readiness</div>
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '14px', fontWeight: 600 }}>Overall Completion</span>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--brand)' }}>{Math.round(overall)}%</span>
          </div>
          <ProgressBar value={overall} showLabel />
          {overall < 80 && (
            <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: 10 }}>
              A complete profile means fewer questions during application. 
            </p>
          )}
          <div style={{ marginTop: '16px', display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            {pausedSessions > 0 && (
              <Button variant="outline" size="sm" onClick={() => navigate('/applications')} leftIcon={<Clock size={14} />}>
                {pausedSessions} paused session{pausedSessions > 1 ? 's' : ''}
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => navigate('/profile')}>
              Manage Profile
            </Button>
          </div>
        </Card>

      </div>
    </AppLayout>
  )
}
