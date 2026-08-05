import { useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { applicationsApi } from '../../api/applications';
import { useApplicationSocket, type AgentEvent } from '../../hooks/useApplicationSocket';
import { useApplicationStore } from '../../stores/applicationStore';
import { useAuthStore } from '../../stores/authStore';
import {
  AlertTriangle, CheckCircle, Loader2, Square, ChevronRight
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const WORKFLOW_STEPS = [
  'Search', 'Select Job', 'Open Page', 'Login', 'Extract', 'Fill', 'Review'
];

export default function ProgressPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const accessToken = useAuthStore(s => s.accessToken);
  const messages = useApplicationStore(s => s.messages);
  const status = useApplicationStore(s => s.status);
  const manualActionRequired = useApplicationStore(s => s.manualActionRequired);
  const manualActionInstructions = useApplicationStore(s => s.manualActionInstructions);
  const clearManualAction = useApplicationStore(s => s.clearManualAction);
  const setStatus = useApplicationStore(s => s.setStatus);
  const setCurrentNode = useApplicationStore(s => s.setCurrentNode);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => applicationsApi.get(sessionId!),
    enabled: !!sessionId,
    refetchInterval: 5000,
  });

  const continueMutation = useMutation({
    mutationFn: () => applicationsApi.continueSession(sessionId!),
    onSuccess: () => { clearManualAction(); setStatus('navigating'); },
  });

  const stopMutation = useMutation({
    mutationFn: () => applicationsApi.stopSession(sessionId!),
    onSuccess: () => navigate('/dashboard'),
  });

  useApplicationSocket({
    sessionId: sessionId!,
    accessToken: accessToken!,
    enabled: !!sessionId && !!accessToken,
    onEvent: (event: AgentEvent) => {
      if (event.type === 'review_ready') navigate(`/applications/${sessionId}/review`);
      if (event.type === 'questions_ready') navigate(`/applications/${sessionId}/questions`);
      if (event.type === 'jobs_found') navigate(`/applications/${sessionId}/jobs`);
      if (event.node) setCurrentNode(event.node);
      if (event.type === 'manual_action_required') {
        useApplicationStore.getState().setManualAction(event.reason || null, event.instructions || null);
      }
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Application Progress</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
            Session #{sessionId?.slice(0, 8)} · Status: <span className="tag tag-warning">{status.toUpperCase()}</span>
          </p>
        </div>

        {/* Stepper */}
        <div className="stepper">
          {WORKFLOW_STEPS.map((step, idx) => (
            <div key={step} className={`step ${idx <= 3 ? 'done' : idx === 4 ? 'active' : ''}`}>
              <div className="circ">{idx <= 3 ? '✓' : idx + 1}</div>
              <div className="lbl">{step}</div>
            </div>
          ))}
        </div>

        {/* Grid-2: Browser View & Agent Log */}
        <div className="grid-2">
          {/* Left Card: Browser Status */}
          <Card>
            <h3 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', marginBottom: '12px' }}>Browser Status</h3>
            <div style={{
              height: '240px',
              backgroundColor: 'var(--ph-bg)',
              border: '1px dashed var(--line)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--muted)',
              fontSize: '13px'
            }}>
              [ Live browser view — {session?.company || 'Employer Careers Page'} ]
            </div>

            <div className="lock-banner" style={{ marginTop: '16px' }}>
              🔒 Manual action required — agent will not enter credentials automatically.
            </div>

            {manualActionRequired && (
              <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                <Button
                  isLoading={continueMutation.isPending}
                  onClick={() => continueMutation.mutate()}
                  rightIcon={<ChevronRight size={16} />}
                >
                  Continue Session
                </Button>
              </div>
            )}
          </Card>

          {/* Right Card: Agent Log */}
          <Card>
            <h3 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', marginBottom: '12px' }}>Agent Log</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '320px', overflowY: 'auto' }}>
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>
                  Connecting to agent…
                </div>
              ) : (
                messages.map(msg => (
                  <div key={msg.id} style={{ padding: '10px', backgroundColor: 'rgba(31,42,40,0.03)', borderRadius: '6px', fontSize: '13px', border: '1px solid var(--line-soft)' }}>
                    <strong>AGENT — </strong> {msg.text}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <Button variant="danger" size="sm" onClick={() => stopMutation.mutate()} isLoading={stopMutation.isPending} leftIcon={<Square size={14} />}>
                Stop
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
