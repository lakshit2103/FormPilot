import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { applicationsApi } from '../../api/applications';
import { Briefcase, Clock, Play, Eye, Loader2, Plus } from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function HistoryPage() {
  const navigate = useNavigate();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: applicationsApi.list,
  });

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Application History</h1>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
              {sessions?.length || 0} application session(s)
            </p>
          </div>
          <Button onClick={() => navigate('/dashboard')} leftIcon={<Plus size={16} />}>
            New Application
          </Button>
        </div>

        {isLoading && (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Loader2 size={32} style={{ margin: '0 auto', animation: 'spin 1s linear infinite', color: 'var(--brand)' }} />
          </div>
        )}

        {!isLoading && (!sessions || sessions.length === 0) && (
          <Card style={{ textAlign: 'center', padding: '48px' }}>
            <Briefcase size={48} style={{ margin: '0 auto 16px', color: 'var(--muted)' }} />
            <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>No applications yet</h3>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>Start your first job application from the dashboard.</p>
            <Button onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </Card>
        )}

        {sessions && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Company & Role</th>
                <th>Query</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(session => {
                const canResume = ['paused', 'asking', 'navigating'].includes(session.status);
                const canReview = session.status === 'reviewing' || session.status === 'complete';

                return (
                  <tr key={session.id}>
                    <td>
                      <strong>{session.company || 'Unknown Company'}</strong> — {session.role || 'Role'}
                    </td>
                    <td style={{ color: 'var(--muted)' }}>"{session.user_query.slice(0, 50)}…"</td>
                    <td>{format(new Date(session.created_at), 'MMM d, yyyy')}</td>
                    <td>
                      <span className={`tag ${session.status === 'complete' ? 'tag-success' : 'tag-warning'}`}>
                        {session.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {canResume && (
                          <Button size="sm" onClick={() => navigate(`/applications/${session.id}/progress`)} leftIcon={<Play size={12} />}>
                            Resume
                          </Button>
                        )}
                        {canReview && (
                          <Button size="sm" variant="outline" onClick={() => navigate(`/applications/${session.id}/review`)} leftIcon={<Eye size={12} />}>
                            Review
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => navigate(`/applications/${session.id}/jobs`)}>
                          Jobs
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </AppLayout>
  );
}
