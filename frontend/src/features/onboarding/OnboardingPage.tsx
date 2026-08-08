import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PhoneInput } from 'react-international-phone'
import 'react-international-phone/style.css'
import {
  User, Phone, MapPin, GraduationCap, Briefcase, Code2,
  FolderGit2, Award, Settings2, Link2, FileText,
  ChevronRight, ChevronLeft, Bot, CheckCircle2, Save, Upload, Plus, Trash2
} from 'lucide-react'
import { profileApi } from '@/api/profile'
import { documentsApi } from '@/api/documents'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Input, Textarea } from '@/components/ui/Input'
import { useToast } from '@/components/ui/Toast'
import { ProgressBar } from '@/components/ui/Loaders'

const STEPS = [
  { id: 'personal', label: 'Personal', icon: User },
  { id: 'addresses', label: 'Address', icon: MapPin },
  { id: 'education', label: 'Education', icon: GraduationCap },
  { id: 'experience', label: 'Experience', icon: Briefcase },
  { id: 'skills', label: 'Skills', icon: Code2 },
  { id: 'projects', label: 'Projects', icon: FolderGit2 },
  { id: 'certifications', label: 'Certs', icon: Award },
  { id: 'preferences', label: 'Preferences', icon: Settings2 },
  { id: 'professional_links', label: 'Links', icon: Link2 },
  { id: 'documents', label: 'Documents', icon: FileText },
]

// ── Step 1: Personal
function PersonalStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const [phone, setPhone] = useState('')

  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.updateProfile({ ...data, primary_phone: phone }),
    onSuccess: () => { toast('Personal info saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save', 'error'),
  })

  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <div className="grid-2">
        <Input label="First name" id="ob-first" required {...register('first_name')} />
        <Input label="Last name" id="ob-last" required {...register('last_name')} />
      </div>

      <div className="input-group">
        <label className="input-label">Contact Number *</label>
        <PhoneInput
          defaultCountry="in"
          value={phone}
          onChange={(val) => setPhone(val)}
          inputStyle={{
            width: '100%',
            height: '42px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--line)',
            borderRadius: '0 8px 8px 0',
            fontSize: '14px',
            color: 'var(--text)',
          }}
          countrySelectorStyleProps={{
            buttonStyle: {
              height: '42px',
              backgroundColor: 'var(--ph-bg)',
              border: '1px solid var(--line)',
              borderRadius: '8px 0 0 8px',
              padding: '0 8px'
            }
          }}
        />
      </div>

      <Input label="Middle name" id="ob-middle" {...register('middle_name')} />
      <Input label="Preferred name" id="ob-preferred" hint="What you'd like to be called" {...register('preferred_name')} />
      <div className="grid-2">
        <Input label="Date of birth" type="date" id="ob-dob" {...register('date_of_birth')} />
        <div className="input-group">
          <label className="input-label">Gender</label>
          <select id="ob-gender" className="input-field" {...register('gender')}>
            <option value="">Select…</option>
            {['Male', 'Female', 'Non-binary', 'Prefer not to say'].map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
      </div>
      <Input label="Nationality" id="ob-nationality" placeholder="Indian" {...register('nationality')} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 3: Address
function AddressStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createAddress(data),
    onSuccess: () => { toast('Address saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save address', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <Input label="Address Line 1" id="ob-addr1" placeholder="Flat / House No., Building Name" required {...register('address_line_1')} />
      <Input label="Address Line 2" id="ob-addr2" placeholder="Street, Area, Landmark" {...register('address_line_2')} />
      <div className="grid-2">
        <Input label="City" id="ob-addr-city" placeholder="Bangalore" required {...register('city')} />
        <Input label="State" id="ob-addr-state" placeholder="Karnataka" required {...register('state')} />
      </div>
      <div className="grid-2">
        <Input label="Country" id="ob-addr-country" defaultValue="India" {...register('country')} />
        <Input label="Postal Code" id="ob-addr-postal" placeholder="560001" required {...register('postal_code')} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 4: Education
function EducationStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createEducation(data),
    onSuccess: () => { toast('Education details saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save education', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <div className="grid-2">
        <Input label="Degree / Qualification" id="ob-edu-degree" placeholder="B.Tech Computer Science" required {...register('degree')} />
        <Input label="Institution / College Name" id="ob-edu-inst" placeholder="IIT Delhi" required {...register('institution_name')} />
      </div>
      <div className="grid-2">
        <Input label="Board / University" id="ob-edu-univ" placeholder="AKTU / VTU" {...register('board_or_university')} />
        <Input label="Specialisation" id="ob-edu-spec" placeholder="Artificial Intelligence" {...register('specialisation')} />
      </div>
      <div className="grid-2">
        <Input label="Start Date" type="date" id="ob-edu-start" {...register('start_date')} />
        <Input label="End Date" type="date" id="ob-edu-end" {...register('end_date')} />
      </div>
      <div className="grid-2">
        <Input label="CGPA / Percentage" id="ob-edu-cgpa" placeholder="8.5 or 85%" {...register('cgpa')} />
        <div style={{ display: 'flex', alignItems: 'center', marginTop: '24px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
            <input type="checkbox" {...register('is_current')} />
            Currently studying here
          </label>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 5: Experience
function ExperienceStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createExperience(data),
    onSuccess: () => { toast('Work experience saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save experience', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <div className="grid-2">
        <Input label="Company Name" id="ob-exp-comp" placeholder="Google / TCS" required {...register('company_name')} />
        <Input label="Job Title" id="ob-exp-title" placeholder="Software Engineer" required {...register('job_title')} />
      </div>
      <div className="grid-2">
        <Input label="Location" id="ob-exp-loc" placeholder="Bangalore, India" {...register('location')} />
        <div className="input-group">
          <label className="input-label">Employment Type</label>
          <select id="ob-exp-type" className="input-field" {...register('employment_type')}>
            <option value="Full-time">Full-time</option>
            <option value="Part-time">Part-time</option>
            <option value="Internship">Internship</option>
            <option value="Contract">Contract</option>
          </select>
        </div>
      </div>
      <div className="grid-2">
        <Input label="Start Date" type="date" id="ob-exp-start" {...register('start_date')} />
        <Input label="End Date" type="date" id="ob-exp-end" {...register('end_date')} />
      </div>
      <Textarea label="Description / Key Achievements" id="ob-exp-desc" placeholder="Describe your roles, responsibilities, and key accomplishments..." {...register('description')} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 6: Skills
function SkillsStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset } = useForm()
  const { data: skills = [] } = useQuery({ queryKey: ['skills'], queryFn: () => profileApi.listSkills().then(r => r.data) })

  const createMutation = useMutation({
    mutationFn: (data: any) => profileApi.createSkill(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['skills'] }); reset(); toast('Skill added ✓', 'success') },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteSkill(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['skills'] }),
  })

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px', minHeight: '40px' }}>
        {skills.map((s: any) => (
          <div key={s.id} className="tag" style={{ display: 'flex', gap: '6px', alignItems: 'center', padding: '6px 12px' }}>
            <span>{s.skill_name}</span>
            {s.proficiency_level && <span style={{ color: 'var(--brand)', fontSize: '10px' }}>({s.proficiency_level})</span>}
            <button type="button" onClick={() => deleteMutation.mutate(s.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(d => createMutation.mutate(d))} style={{ borderTop: '1px solid var(--line)', paddingTop: '16px' }}>
        <div className="grid-2">
          <Input label="Skill Name" id="ob-skill-name" placeholder="e.g. Python, React, PyTorch" required {...register('skill_name')} />
          <div className="input-group">
            <label className="input-label">Proficiency Level</label>
            <select id="ob-skill-level" className="input-field" {...register('proficiency_level')}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
          <Button type="submit" variant="outline" isLoading={createMutation.isPending} leftIcon={<Plus size={14} />}>
            Add Skill
          </Button>
          <Button type="button" onClick={onNext} rightIcon={<ChevronRight size={16} />}>
            Continue
          </Button>
        </div>
      </form>
    </div>
  )
}

// ── Step 7: Projects
function ProjectsStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createProject(data),
    onSuccess: () => { toast('Project saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save project', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <Input label="Project Title" id="ob-proj-title" placeholder="FormPilot AI Assistant" required {...register('title')} />
      <Textarea label="Project Description" id="ob-proj-desc" placeholder="Brief summary of the project and its core features..." {...register('description')} />
      <Input label="Technologies Used" id="ob-proj-tech" placeholder="Python, FastAPI, React, PostgreSQL" {...register('technologies')} />
      <div className="grid-2">
        <Input label="Project URL" id="ob-proj-url" placeholder="https://formpilot.ai" {...register('project_url')} />
        <Input label="GitHub / Repo URL" id="ob-proj-repo" placeholder="https://github.com/user/project" {...register('repository_url')} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 8: Certifications
function CertificationsStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createCertification(data),
    onSuccess: () => { toast('Certification saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save certification', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <Input label="Certification Name" id="ob-cert-name" placeholder="AWS Certified Solutions Architect" required {...register('name')} />
      <Input label="Issuing Organization" id="ob-cert-org" placeholder="Amazon Web Services" {...register('issuing_organization')} />
      <div className="grid-2">
        <Input label="Issue Date" type="date" id="ob-cert-issue" {...register('issue_date')} />
        <Input label="Expiry Date" type="date" id="ob-cert-expiry" {...register('expiry_date')} />
      </div>
      <Input label="Credential ID" id="ob-cert-id" placeholder="ABC123XYZ" {...register('credential_id')} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 9: Preferences
function PreferencesStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.updatePreferences(data),
    onSuccess: () => { toast('Job preferences saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save preferences', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <div className="grid-2">
        <Input label="Notice Period" id="ob-pref-notice" placeholder="30 days / Immediate" {...register('notice_period')} />
        <Input label="Expected Annual Salary (INR)" type="number" id="ob-pref-salary" placeholder="1200000" {...register('expected_salary')} />
      </div>
      <div className="grid-2">
        <Input label="Preferred Locations" id="ob-pref-locs" placeholder="Bangalore, Remote, Hyderabad" {...register('preferred_locations')} />
        <Input label="Shift Preference" id="ob-pref-shift" placeholder="Day Shift / Flexible" {...register('shift_preference')} />
      </div>
      <div style={{ display: 'flex', gap: '20px', marginTop: '16px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
          <input type="checkbox" {...register('willing_to_relocate')} /> Willing to relocate
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
          <input type="checkbox" {...register('willing_to_travel')} /> Willing to travel
        </label>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 10: Links
function LinksStep({ onNext }: { onNext: () => void }) {
  const { toast } = useToast()
  const { register, handleSubmit } = useForm()
  const mutation = useMutation({
    mutationFn: (data: any) => profileApi.createLink(data),
    onSuccess: () => { toast('Professional link saved ✓', 'success'); onNext() },
    onError: () => toast('Failed to save link', 'error'),
  })
  return (
    <form onSubmit={handleSubmit(d => mutation.mutate(d))}>
      <div className="grid-2">
        <div className="input-group">
          <label className="input-label">Platform</label>
          <select id="ob-link-platform" className="input-field" {...register('platform')}>
            <option value="LinkedIn">LinkedIn</option>
            <option value="GitHub">GitHub</option>
            <option value="Portfolio">Portfolio Website</option>
            <option value="Twitter">Twitter / X</option>
            <option value="LeetCode">LeetCode</option>
          </select>
        </div>
        <Input label="Profile / Portfolio URL" id="ob-link-url" placeholder="https://linkedin.com/in/username" required {...register('url')} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <Button type="submit" isLoading={mutation.isPending} rightIcon={<ChevronRight size={16} />}>
          Save & Continue
        </Button>
      </div>
    </form>
  )
}

// ── Step 11: Documents
function DocumentsStep({ onComplete }: { onComplete: () => void }) {
  const { toast } = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleUpload = async () => {
    if (!file) return onComplete()
    setUploading(true)
    try {
      await documentsApi.upload('resume', file)
      toast('Resume uploaded successfully! 🎉', 'success')
      onComplete()
    } catch {
      toast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ textAlign: 'center', padding: '24px' }}>
      <div style={{ border: '2px dashed var(--line)', padding: '36px', borderRadius: '12px', marginBottom: '24px', cursor: 'pointer' }}>
        <Upload size={40} style={{ color: 'var(--brand)', margin: '0 auto 12px' }} />
        <p style={{ fontWeight: 600, fontSize: '15px' }}>Upload your latest Resume / CV</p>
        <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>PDF or DOCX format · Max 5 MB</p>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={e => setFile(e.target.files?.[0] || null)}
          style={{ marginTop: '16px' }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
        <Button size="lg" isLoading={uploading} onClick={handleUpload}>
          {file ? 'Upload & Complete Setup 🚀' : 'Complete Setup 🚀'}
        </Button>
      </div>
    </div>
  )
}

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const { setUser, user } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()

  const progress = ((currentStep) / STEPS.length) * 100

  const goNext = () => {
    if (currentStep < STEPS.length - 1) setCurrentStep(s => s + 1)
    else handleComplete()
  }
  const goBack = () => setCurrentStep(s => Math.max(0, s - 1))

  const handleComplete = async () => {
    try {
      await apiClient.post('/api/onboarding/complete')
    } catch {
      // Non-blocking — still navigate even if the call fails
    }
    if (user) setUser({ ...user, setup_complete: true })
    toast('Profile setup complete! 🎉', 'success')
    navigate('/dashboard', { replace: true })
  }

  const stepId = STEPS[currentStep].id
  const StepIcon = STEPS[currentStep].icon

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Left Sidebar */}
      <div style={{ width: '280px', flexShrink: 0, backgroundColor: 'var(--panel-strong)', borderRight: '1px solid var(--line)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ display: 'flex', itemsCenter: 'center', gap: '12px', marginBottom: '20px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
              <Bot size={24} />
            </div>
            <span style={{ fontWeight: 700, fontSize: '18px', color: 'var(--brand)' }}>FormPilot AI</span>
          </div>
          <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Account Setup</h2>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>Step {currentStep + 1} of {STEPS.length}</p>
          <ProgressBar value={progress} className="mt-3" />
        </div>

        <nav style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
          {STEPS.map((step, i) => {
            const Icon = step.icon
            const done = i < currentStep
            const active = i === currentStep
            return (
              <button
                key={step.id}
                onClick={() => setCurrentStep(i)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  border: 'none',
                  background: active ? 'var(--brand-light)' : 'transparent',
                  color: active ? 'var(--brand)' : done ? 'var(--green)' : 'var(--muted)',
                  fontWeight: active ? 600 : 400,
                  cursor: 'pointer',
                  marginBottom: '4px',
                  textAlign: 'left',
                }}
                aria-label={`Go to ${step.label} step`}
              >
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: active ? 'var(--brand)' : done ? 'rgba(47, 111, 79, 0.15)' : 'var(--ph-bg)',
                  color: active ? '#fff' : done ? 'var(--green)' : 'var(--muted)',
                }}>
                  {done ? <CheckCircle2 size={16} /> : <Icon size={16} />}
                </div>
                {step.label}
              </button>
            )
          })}
        </nav>

        <div style={{ padding: '16px', borderTop: '1px solid var(--line)' }}>
          <Button variant="ghost" size="sm" style={{ width: '100%' }} onClick={() => navigate('/dashboard')}>
            <Save size={16} /> Save & exit
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '40px', overflowY: 'auto', display: 'flex', justifyContent: 'center' }}>
        <div style={{ width: '100%', maxWidth: '640px' }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'var(--brand-light)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--brand)' }}>
              <StepIcon size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 700 }}>{STEPS[currentStep].label}</h1>
              <p style={{ fontSize: '14px', color: 'var(--muted)' }}>Step {currentStep + 1} of {STEPS.length}</p>
            </div>
          </div>

          {/* Form Card */}
          <div className="glass-card animate-slide-up" style={{ padding: '32px' }}>
            {stepId === 'personal' && <PersonalStep onNext={goNext} />}
            {stepId === 'addresses' && <AddressStep onNext={goNext} />}
            {stepId === 'education' && <EducationStep onNext={goNext} />}
            {stepId === 'experience' && <ExperienceStep onNext={goNext} />}
            {stepId === 'skills' && <SkillsStep onNext={goNext} />}
            {stepId === 'projects' && <ProjectsStep onNext={goNext} />}
            {stepId === 'certifications' && <CertificationsStep onNext={goNext} />}
            {stepId === 'preferences' && <PreferencesStep onNext={goNext} />}
            {stepId === 'professional_links' && <LinksStep onNext={goNext} />}
            {stepId === 'documents' && <DocumentsStep onComplete={handleComplete} />}

            {currentStep > 0 && (
              <button
                type="button"
                onClick={goBack}
                style={{ marginTop: '20px', background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px' }}
              >
                <ChevronLeft size={16} /> Back
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
