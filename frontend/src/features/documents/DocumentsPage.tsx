import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Star, Trash2, Download, File, Plus } from 'lucide-react'
import { documentsApi } from '@/api/documents'
import { useToast } from '@/components/ui/Toast'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Card, CardHeader } from '@/components/ui/Card'
import { AppLayout } from '@/components/layout/AppLayout'
import { formatBytes, formatDate } from '@/utils/cn'

const DOCUMENT_TYPES = [
  { value: 'resume', label: 'Resume', accept: '.pdf,.docx' },
  { value: 'cover_letter', label: 'Cover Letter', accept: '.pdf,.docx' },
  { value: 'photograph', label: 'Photograph', accept: '.jpg,.jpeg,.png,.webp' },
  { value: 'marksheet', label: 'Marksheet', accept: '.pdf,.jpg,.jpeg,.png' },
  { value: 'degree_cert', label: 'Degree Certificate', accept: '.pdf,.jpg,.jpeg,.png' },
  { value: 'internship_cert', label: 'Internship Certificate', accept: '.pdf,.jpg,.jpeg,.png' },
  { value: 'experience_letter', label: 'Experience Letter', accept: '.pdf,.jpg,.jpeg,.png' },
  { value: 'other', label: 'Other', accept: '.pdf,.jpg,.jpeg,.png,.docx,.webp' },
]

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [uploadModal, setUploadModal] = useState(false)
  const [docType, setDocType] = useState('resume')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const { data: docs = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list().then(r => r.data),
  })

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => documentsApi.setDefault(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['documents'] }); toast('Default document updated', 'success') },
    onError: () => toast('Failed to update default', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['documents'] }); setDeleteId(null); toast('Document deleted', 'success') },
    onError: () => toast('Failed to delete document', 'error'),
  })

  const onDrop = useCallback(async (files: File[]) => {
    if (!files[0]) return
    setUploading(true)
    try {
      await documentsApi.upload(docType, files[0])
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast('Document uploaded successfully!', 'success')
      setUploadModal(false)
    } catch (err: any) {
      toast(err?.response?.data?.detail || 'Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }, [docType, queryClient, toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, multiple: false, maxSize: 5 * 1024 * 1024,
  })

  const groupedDocs = DOCUMENT_TYPES.reduce((acc, t) => {
    const items = docs.filter((d: any) => d.document_type === t.value)
    if (items.length) acc[t.value] = { label: t.label, items }
    return acc
  }, {} as Record<string, { label: string; items: any[] }>)

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700 }}>My Documents</h1>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>Upload and manage your resumes, certificates, and more</p>
          </div>
          <Button id="upload-doc-btn" leftIcon={<Plus size={16} />} onClick={() => setUploadModal(true)}>
            Upload Document
          </Button>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>Loading documents…</div>
        ) : docs.length === 0 ? (
          <Card style={{ textAlign: 'center', padding: '48px' }}>
            <FileText size={48} style={{ color: 'var(--muted)', margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>No documents yet</h3>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>Upload your resume to get started with automatic form filling</p>
            <Button onClick={() => setUploadModal(true)} leftIcon={<Upload size={16} />}>
              Upload your resume
            </Button>
          </Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {Object.entries(groupedDocs).map(([type, { label, items }]) => (
              <Card key={type}>
                <CardHeader title={label} subtitle={`${items.length} file${items.length !== 1 ? 's' : ''}`} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {items.map((doc: any) => (
                    <div
                      key={doc.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px',
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid var(--line)',
                        backgroundColor: doc.is_default ? 'var(--brand-light)' : '#ffffff',
                      }}
                    >
                      <div style={{ width: '40px', height: '40px', borderRadius: '8px', backgroundColor: 'var(--ph-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
                        <File size={20} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <p style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--text)' }}>{doc.file_name}</p>
                          {doc.is_default && (
                            <span className="tag tag-success" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <Star size={10} /> Default
                            </span>
                          )}
                        </div>
                        <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px', margin: 0 }}>
                          {formatBytes(doc.file_size)} · {formatDate(doc.created_at)}
                        </p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {!doc.is_default && (
                          <button
                            onClick={() => setDefaultMutation.mutate(doc.id)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: '6px' }}
                            title="Set as default"
                          >
                            <Star size={16} />
                          </button>
                        )}
                        <a
                          href={documentsApi.downloadUrl(doc.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--brand)', padding: '6px' }}
                        >
                          <Download size={16} />
                        </a>
                        <button
                          onClick={() => setDeleteId(doc.id)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--rose)', padding: '6px' }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Upload Modal */}
        <Modal isOpen={uploadModal} onClose={() => setUploadModal(false)} title="Upload Document" size="md">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="input-group">
              <label className="input-label">Document Type</label>
              <select
                id="doc-type-select"
                value={docType}
                onChange={e => setDocType(e.target.value)}
                className="input-field"
              >
                {DOCUMENT_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div
              {...getRootProps()}
              style={{
                border: '2px dashed var(--line)',
                borderRadius: '12px',
                padding: '40px',
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? 'var(--brand-light)' : 'transparent',
              }}
            >
              <input {...getInputProps()} id="file-dropzone" aria-label="File upload dropzone" />
              <Upload size={36} style={{ color: isDragActive ? 'var(--brand)' : 'var(--muted)', margin: '0 auto 12px' }} />
              {isDragActive ? (
                <p style={{ color: 'var(--brand)', fontWeight: 600 }}>Drop it here!</p>
              ) : (
                <>
                  <p style={{ fontWeight: 600, color: 'var(--text)', margin: 0 }}>Drag & drop a file here</p>
                  <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>or click to browse · Max 5 MB</p>
                </>
              )}
            </div>

            {uploading && <div style={{ textAlign: 'center', fontSize: '14px', color: 'var(--brand)' }}>Uploading…</div>}
          </div>
        </Modal>

        {/* Delete Confirmation */}
        <Modal isOpen={!!deleteId} onClose={() => setDeleteId(null)} title="Delete Document" size="sm">
          <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>Are you sure you want to delete this document? This cannot be undone.</p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="ghost" style={{ flex: 1 }} onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button
              variant="danger"
              style={{ flex: 1 }}
              isLoading={deleteMutation.isPending}
              onClick={() => deleteId && deleteMutation.mutate(deleteId)}
              id="confirm-delete-doc"
            >
              Delete
            </Button>
          </div>
        </Modal>
      </div>
    </AppLayout>
  )
}
