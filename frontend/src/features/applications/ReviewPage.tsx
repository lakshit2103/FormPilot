import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { applicationsApi, type FieldMapping } from '../../api/applications';
import {
  CheckCircle2, AlertTriangle, XCircle, Edit3, RotateCcw,
  ShieldOff, Loader2, FileText
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function ReviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const { data: review, isLoading, refetch } = useQuery({
    queryKey: ['review', sessionId],
    queryFn: () => applicationsApi.getReview(sessionId!),
    enabled: !!sessionId,
  });

  const editMutation = useMutation({
    mutationFn: ({ fieldId, value }: { fieldId: string; value: string }) =>
      applicationsApi.editField(sessionId!, fieldId, value),
    onSuccess: () => { setEditingId(null); refetch(); },
  });

  const revalidateMutation = useMutation({
    mutationFn: () => applicationsApi.revalidate(sessionId!),
    onSuccess: () => refetch(),
  });

  if (isLoading || !review) {
    return (
      <AppLayout>
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', margin: '0 auto', color: 'var(--brand)' }} />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Review Dashboard</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
            Review all filled fields before final submission.
          </p>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid-4">
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Total Fields</div>
            <div style={{ fontSize: '22px', fontWeight: 700, marginTop: '4px', color: 'var(--text)' }}>{review.total_fields}</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Auto-filled</div>
            <div style={{ fontSize: '22px', fontWeight: 700, marginTop: '4px', color: 'var(--green)' }}>{review.auto_filled}</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>User Answers</div>
            <div style={{ fontSize: '22px', fontWeight: 700, marginTop: '4px', color: 'var(--brand)' }}>{review.user_provided}</div>
          </Card>
          <Card>
            <div style={{ fontSize: '12px', color: 'var(--muted)', textTransform: 'uppercase' }}>Errors</div>
            <div style={{ fontSize: '22px', fontWeight: 700, marginTop: '4px', color: 'var(--rose)' }}>{review.errors}</div>
          </Card>
        </div>

        {/* Filled Fields Table */}
        <div className="section-title">Filled fields</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
              <th>Source</th>
              <th>Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {review.mappings.map((mapping: FieldMapping) => {
              const isEditing = editingId === mapping.id;

              return (
                <tr key={mapping.id}>
                  <td><strong>{mapping.profile_key || 'Field'}</strong></td>
                  <td>
                    {isEditing ? (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input
                          value={editValue}
                          onChange={e => setEditValue(e.target.value)}
                          className="input-field"
                          style={{ padding: '4px 8px', fontSize: '13px' }}
                        />
                        <Button size="sm" onClick={() => editMutation.mutate({ fieldId: mapping.id, value: editValue })}>Save</Button>
                      </div>
                    ) : (
                      mapping.proposed_value || <span style={{ color: 'var(--muted)', fontStyle: 'italic' }}>Empty</span>
                    )}
                  </td>
                  <td><span className="tag">{mapping.profile_source || 'Profile'}</span></td>
                  <td>
                    <span className={`tag ${mapping.confidence && mapping.confidence > 0.8 ? 'tag-success' : 'tag-warning'}`}>
                      {mapping.confidence ? `${Math.round(mapping.confidence * 100)}%` : 'Manual'}
                    </span>
                  </td>
                  <td>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => { setEditingId(mapping.id); setEditValue(mapping.proposed_value || ''); }}
                    >
                      Edit
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Lock Banner */}
        <div className="lock-banner" style={{ marginTop: '12px' }}>
          🔒 FormPilot AI will not submit this application automatically. Review carefully, then submit manually on the employer's site.
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
          <Button variant="outline" onClick={() => revalidateMutation.mutate()} isLoading={revalidateMutation.isPending} leftIcon={<RotateCcw size={16} />}>
            Revalidate
          </Button>
          <Button disabled style={{ opacity: 0.5 }}>
            Final Submit — disabled in MVP
          </Button>
        </div>
      </div>
    </AppLayout>
  );
}
