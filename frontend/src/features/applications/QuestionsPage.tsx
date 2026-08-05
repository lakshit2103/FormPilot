import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { applicationsApi, type MissingQuestion, type AnswerPayload } from '../../api/applications';
import { CheckCircle, Loader2 } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

type SaveMode = 'use_once' | 'save_to_profile' | 'replace_default';

export default function QuestionsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const { data: questions, isLoading } = useQuery({
    queryKey: ['questions', sessionId],
    queryFn: () => applicationsApi.getQuestions(sessionId!),
    enabled: !!sessionId,
  });

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [saveModes, setSaveModes] = useState<Record<string, SaveMode>>({});

  const submitMutation = useMutation({
    mutationFn: (payload: AnswerPayload[]) => applicationsApi.submitAnswers(sessionId!, payload),
    onSuccess: () => navigate(`/applications/${sessionId}/progress`),
  });

  const handleSubmit = () => {
    const payload: AnswerPayload[] = (questions || []).map(q => ({
      question_id: q.id,
      answer_value: answers[q.id] || '',
      save_to_profile: saveModes[q.id] || 'use_once',
    }));
    submitMutation.mutate(payload);
  };

  const setAnswer = (id: string, value: string) => setAnswers(p => ({ ...p, [id]: value }));
  const setSaveMode = (id: string, mode: SaveMode) => setSaveModes(p => ({ ...p, [id]: mode }));

  if (isLoading) {
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
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Missing Information</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
            Answer the questions below so FormPilot AI can complete your application.
          </p>
        </div>

        <div className="callout">
          The form asked {questions?.length || 0} question(s) that aren't in your profile yet. Answer below to continue.
        </div>

        {questions && questions.map((q, i) => (
          <Card key={q.id}>
            <div style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', marginBottom: '8px' }}>
              Original field label: "{q.question}"
            </div>
            <div className="input-group">
              <label className="input-label">{q.question}</label>
              <input
                type="text"
                value={answers[q.id] || ''}
                onChange={e => setAnswer(q.id, e.target.value)}
                className="input-field"
                placeholder="Type your answer…"
              />
            </div>
            <div style={{ display: 'flex', gap: '16px', marginTop: '12px', fontSize: '13px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name={`save-${q.id}`}
                  checked={(saveModes[q.id] || 'use_once') === 'use_once'}
                  onChange={() => setSaveMode(q.id, 'use_once')}
                />
                Use once
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name={`save-${q.id}`}
                  checked={saveModes[q.id] === 'save_to_profile'}
                  onChange={() => setSaveMode(q.id, 'save_to_profile')}
                />
                Save to profile
              </label>
            </div>
          </Card>
        ))}

        <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
          <Button
            onClick={handleSubmit}
            isLoading={submitMutation.isPending}
            rightIcon={<CheckCircle size={16} />}
          >
            Submit Answers
          </Button>
        </div>
      </div>
    </AppLayout>
  );
}
