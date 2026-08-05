import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  User, Phone, MapPin, GraduationCap, Briefcase, Code2,
  FolderGit2, Award, Settings2, Link2,
  Plus, Edit2, Check, X
} from 'lucide-react'
import { profileApi } from '@/api/profile'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ProgressBar } from '@/components/ui/Loaders'
import { useToast } from '@/components/ui/Toast'

const TABS = [
  { id: 'personal', label: 'Personal', icon: User },
  { id: 'education', label: 'Education', icon: GraduationCap },
  { id: 'experience', label: 'Experience', icon: Briefcase },
  { id: 'skills', label: 'Skills', icon: Code2 },
  { id: 'projects', label: 'Projects', icon: FolderGit2 },
  { id: 'certifications', label: 'Certifications', icon: Award },
  { id: 'addresses', label: 'Addresses', icon: MapPin },
  { id: 'preferences', label: 'Preferences', icon: Settings2 },
  { id: 'links', label: 'Links', icon: Link2 },
]

function PersonalTab() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)

  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: () => profileApi.getProfile().then(r => r.data) })
  const [form, setForm] = useState<Record<string, string>>({})

  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.updateProfile(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['profile'] }); setEditing(false); toast('Profile updated ✓', 'success') },
    onError: () => toast('Failed to save', 'error'),
  })

  if (!profile) return <div style={{ color: 'var(--muted)', fontSize: '14px', padding: '16px 0' }}>Loading…</div>

  const fields = [
    { key: 'first_name', label: 'First name' }, { key: 'middle_name', label: 'Middle name' },
    { key: 'last_name', label: 'Last name' }, { key: 'preferred_name', label: 'Preferred name' },
    { key: 'date_of_birth', label: 'Date of birth' }, { key: 'gender', label: 'Gender' },
    { key: 'nationality', label: 'Nationality' }, { key: 'primary_phone', label: 'Primary phone' },
    { key: 'current_city', label: 'City' }, { key: 'country', label: 'Country' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        {editing ? (
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)} leftIcon={<X size={16} />}>Cancel</Button>
            <Button size="sm" isLoading={mutation.isPending} onClick={() => mutation.mutate(form)} leftIcon={<Check size={16} />}>Save</Button>
          </div>
        ) : (
          <Button size="sm" variant="outline" onClick={() => { setForm(profile); setEditing(true) }} leftIcon={<Edit2 size={16} />}>Edit</Button>
        )}
      </div>
      <div className="grid-2">
        {fields.map(f => (
          <div key={f.key}>
            <p style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>{f.label}</p>
            {editing ? (
              <Input
                id={`profile-${f.key}`}
                value={form[f.key] || ''}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.label}
              />
            ) : (
              <p style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text)' }}>
                {(profile as any)[f.key] || <span style={{ color: 'var(--muted)', fontStyle: 'italic' }}>Not set</span>}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function SkillsTab() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [adding, setAdding] = useState(false)
  const [newSkill, setNewSkill] = useState({ skill_name: '', category: '', proficiency_level: '' })

  const { data: skills = [] } = useQuery({ queryKey: ['skills'], queryFn: () => profileApi.listSkills().then(r => r.data) })

  const createMutation = useMutation({
    mutationFn: (data: any) => profileApi.createSkill(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['skills'] }); setAdding(false); setNewSkill({ skill_name: '', category: '', proficiency_level: '' }); toast('Skill added ✓', 'success') },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteSkill(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['skills'] }); toast('Skill removed', 'success') },
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', minHeight: '40px' }}>
        {skills.map((s: any) => (
          <div key={s.id} className="tag" style={{ display: 'flex', gap: '6px', alignItems: 'center', padding: '6px 12px' }}>
            <span>{s.skill_name}</span>
            {s.proficiency_level && <span style={{ color: 'var(--brand)', fontSize: '10px' }}>({s.proficiency_level})</span>}
            <button
              onClick={() => deleteMutation.mutate(s.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 0 }}
            >
              <X size={12} />
            </button>
          </div>
        ))}
        {skills.length === 0 && <p style={{ color: 'var(--muted)', fontSize: '14px', fontStyle: 'italic' }}>No skills added yet</p>}
      </div>

      {adding ? (
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <Input id="new-skill-name" label="Skill name" value={newSkill.skill_name} onChange={e => setNewSkill(p => ({ ...p, skill_name: e.target.value }))} placeholder="e.g. Python" />
          <div className="input-group">
            <label className="input-label">Level</label>
            <select className="input-field" value={newSkill.proficiency_level} onChange={e => setNewSkill(p => ({ ...p, proficiency_level: e.target.value }))}>
              <option value="">Select…</option>
              {['beginner', 'intermediate', 'advanced', 'expert'].map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <Button size="sm" onClick={() => createMutation.mutate(newSkill)} isLoading={createMutation.isPending}>Add</Button>
          <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>Cancel</Button>
        </div>
      ) : (
        <Button size="sm" variant="outline" onClick={() => setAdding(true)} leftIcon={<Plus size={14} />}>Add Skill</Button>
      )}
    </div>
  )
}

function GenericListTab({ label }: { label: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '32px', border: '1px dashed var(--line)', borderRadius: '12px' }}>
      <p style={{ color: 'var(--muted)', fontSize: '14px' }}>{label} management coming in the next build.</p>
      <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px' }}>Data can be added via the Onboarding wizard.</p>
    </div>
  )
}

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('personal')

  const { data: completionData } = useQuery({
    queryKey: ['profile-completion'],
    queryFn: () => profileApi.getCompletion().then(r => r.data),
  })

  const overall = completionData?.overall_percentage ?? 0

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700 }}>My Profile</h1>
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginTop: '4px' }}>Your reusable application profile</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '14px', color: 'var(--muted)' }}>Overall completion</span>
            <span style={{ fontSize: '20px', fontWeight: 700, color: 'var(--brand)' }}>{Math.round(overall)}%</span>
          </div>
        </div>

        {/* Completion bar */}
        <ProgressBar value={overall} showLabel />

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
          {TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: active ? 600 : 400,
                  border: active ? '1px solid var(--brand)' : '1px solid transparent',
                  background: active ? 'var(--brand-light)' : 'transparent',
                  color: active ? 'var(--brand)' : 'var(--muted)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
                id={`profile-tab-${tab.id}`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Content Card */}
        <Card>
          {activeTab === 'personal' && (
            <div>
              <CardHeader title="Personal Information" icon={<User size={20} />} />
              <PersonalTab />
            </div>
          )}
          {activeTab === 'skills' && (
            <div>
              <CardHeader title="Skills" icon={<Code2 size={20} />} />
              <SkillsTab />
            </div>
          )}
          {activeTab !== 'personal' && activeTab !== 'skills' && (
            <div>
              <CardHeader title={TABS.find(t => t.id === activeTab)?.label || ''} />
              <GenericListTab label={TABS.find(t => t.id === activeTab)?.label || ''} />
            </div>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
