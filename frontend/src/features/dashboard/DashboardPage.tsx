import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Zap, History, FileText, TrendingUp, Sparkles, User, BookOpen, Briefcase, Code2, Star
} from 'lucide-react'
import { profileApi } from '@/api/profile'
import { useAuthStore } from '@/stores/authStore'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ProgressBar } from '@/components/ui/Loaders'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const { data: completionData } = useQuery({
    queryKey: ['profile-completion'],
    queryFn: () => profileApi.getCompletion().then(r => r.data),
  })

  const overall = completionData?.overall_percentage ?? 0
  const sections = completionData?.sections ?? []

  const handleStart = () => {
    if (query.trim()) {
      navigate(`/applications/start?q=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

        {/* Section 1: Natural-language Job Request */}
        <div className="section-title">Natural-language job request</div>
        <Card style={{ backgroundColor: 'var(--panel-strong)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <input
              id="dashboard-query"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleStart()}
              placeholder='e.g. "Find and fill the TCS application form for an Agentic AI Engineer role"'
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
                  background: 'none',
                  border: '1px solid var(--line)',
                  borderRadius: '4px',
                  padding: '4px 10px',
                  fontSize: '12px',
                  color: 'var(--muted)',
                  cursor: 'pointer'
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </Card>

        {/* Section 2: Quick Stats Grid */}
        <div className="section-title">Quick stats</div>
        <div className="grid-4">
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Applications Started</div>
            <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px', color: 'var(--brand)' }}>12</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Completed</div>
            <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px', color: 'var(--green)' }}>4</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Profile Completion</div>
            <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px', color: 'var(--brand)' }}>{Math.round(overall)}%</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Saved Documents</div>
            <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px', color: 'var(--amber)' }}>3</div>
          </Card>
        </div>

        {/* Section 3: Recent Applications */}
        <div className="section-title">Recent applications</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>TCS</td>
              <td>Agentic AI Engineer</td>
              <td><span className="tag tag-warning">In Review</span></td>
              <td>Today</td>
              <td><Button variant="outline" size="sm" onClick={() => navigate('/applications')}>Open</Button></td>
            </tr>
            <tr>
              <td>Infosys</td>
              <td>Python Developer</td>
              <td><span className="tag tag-success">Completed</span></td>
              <td>Yesterday</td>
              <td><Button variant="ghost" size="sm" onClick={() => navigate('/applications')}>View</Button></td>
            </tr>
          </tbody>
        </table>

        {/* Section 4: Profile Completion Detail */}
        <div className="section-title">Profile Progress</div>
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '14px', fontWeight: 600 }}>Overall Readiness</span>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--brand)' }}>{Math.round(overall)}%</span>
          </div>
          <ProgressBar value={overall} showLabel />
          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="outline" size="sm" onClick={() => navigate('/profile')}>
              Manage Profile
            </Button>
          </div>
        </Card>

      </div>
    </AppLayout>
  )
}
