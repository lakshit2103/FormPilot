import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { History } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useNavigate } from 'react-router-dom'

export default function ApplicationsPage() {
  const navigate = useNavigate()

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Applications</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>Track your job applications and automated sessions</p>
        </div>

        <Card style={{ textAlign: 'center', padding: '60px 24px' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '14px', backgroundColor: 'var(--brand-light)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: 'var(--brand)' }}>
            <History size={28} />
          </div>
          <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>Start an application</h3>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>
            When you enter a natural-language job request on the Dashboard,<br />your application search and fill session will appear here.
          </p>
          <Button onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </Button>
        </Card>
      </div>
    </AppLayout>
  )
}
