import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { applicationsApi, type JobResult } from '../../api/applications';
import { useApplicationStore } from '../../stores/applicationStore';
import {
  ExternalLink, Building2, MapPin, Globe, ChevronRight, Loader2, Link2
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function JobResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const selectJobStore = useApplicationStore(s => s.selectJob);
  const [selectingJobId, setSelectingJobId] = useState<string | null>(null);
  const [manualUrl, setManualUrl] = useState('');

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', sessionId],
    queryFn: () => applicationsApi.getJobs(sessionId!),
    enabled: !!sessionId,
    refetchInterval: 3000,
  });

  const selectMutation = useMutation({
    mutationFn: (jobId: string) => applicationsApi.selectJob(sessionId!, jobId),
    onSuccess: (_, jobId) => {
      const job = jobs?.find(j => j.id === jobId);
      if (job) selectJobStore(job);
      navigate(`/applications/${sessionId}/progress`);
    },
  });

  const urlMutation = useMutation({
    mutationFn: (url: string) => applicationsApi.provideUrl(sessionId!, url),
    onSuccess: () => navigate(`/applications/${sessionId}/progress`),
  });

  const handleSelectJob = (job: JobResult) => {
    setSelectingJobId(job.id);
    selectMutation.mutate(job.id);
  };

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Job Search Results</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>
            {isLoading && !jobs?.length ? 'Searching job portals…' : `${jobs?.length || 0} results found, ranked by relevance`}
          </p>
        </div>

        <div className="callout">
          {jobs?.length ? `Found ${jobs.length} relevant listings. Select a listing below to proceed.` : 'Searching for matching application forms...'}
        </div>

        {isLoading && !jobs?.length && (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', margin: '0 auto', color: 'var(--brand)' }} />
          </div>
        )}

        {jobs && jobs.map(job => {
          const isPending = selectingJobId === job.id && selectMutation.isPending;

          return (
            <Card key={job.id} hover>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                    <span className={`tag ${job.is_official ? 'tag-success' : 'tag-warning'}`}>
                      {job.is_official ? 'Official Source' : '3rd-Party Listing'}
                    </span>
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>{job.title}</h3>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--muted)', marginBottom: '12px' }}>
                    {job.company && <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Building2 size={14} />{job.company}</span>}
                    {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapPin size={14} />{job.location}</span>}
                    {job.domain && <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Globe size={14} />{job.domain}</span>}
                  </div>
                  {job.snippet && (
                    <p style={{ fontSize: '13px', color: 'var(--muted)', margin: 0, lineHeight: 1.5 }}>
                      {job.snippet.slice(0, 180)}…
                    </p>
                  )}
                </div>

                <div style={{ textAlign: 'right', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <Button
                    onClick={() => handleSelectJob(job)}
                    disabled={isPending || job.job_status !== 'available'}
                    isLoading={isPending}
                    rightIcon={<ChevronRight size={16} />}
                  >
                    Select
                  </Button>
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-outline"
                    style={{ fontSize: '12px', padding: '6px 12px' }}
                  >
                    <ExternalLink size={12} /> Open Listing
                  </a>
                </div>
              </div>
            </Card>
          );
        })}

        {/* Section: Manual URL fallback */}
        <div className="section-title">Can't find the right listing?</div>
        <Card>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="url"
              value={manualUrl}
              onChange={e => setManualUrl(e.target.value)}
              placeholder="Paste application URL manually"
              className="input-field"
              style={{ flex: 1 }}
            />
            <Button
              variant="outline"
              disabled={!manualUrl || urlMutation.isPending}
              isLoading={urlMutation.isPending}
              onClick={() => urlMutation.mutate(manualUrl)}
            >
              Use URL
            </Button>
          </div>
        </Card>
      </div>
    </AppLayout>
  );
}
