import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  User, Lock, Monitor, Download, Trash2, ChevronRight,
  LogOut, Shield, AlertTriangle, CheckCircle2
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { settingsApi } from '@/api/settings'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/components/ui/Toast'

type Section = 'account' | 'password' | 'sessions' | 'privacy' | 'danger'

export default function SettingsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { logout } = useAuthStore()
  const { toast } = useToast()
  const [activeSection, setActiveSection] = useState<Section>('account')

  // Account info
  const { data: account, isLoading } = useQuery({
    queryKey: ['settings-account'],
    queryFn: () => settingsApi.getAccount().then(r => r.data),
  })

  // Sessions
  const { data: sessions = [] } = useQuery({
    queryKey: ['settings-sessions'],
    queryFn: () => settingsApi.listSessions().then(r => r.data),
    enabled: activeSection === 'sessions',
  })

  // Mutations
  const updateNameMut = useMutation({
    mutationFn: (name: string) => settingsApi.updateName(name),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['settings-account'] }); toast('Name updated!', 'success') },
    onError: () => toast('Failed to update name', 'error'),
  })

  const changePasswordMut = useMutation({
    mutationFn: ({ current, next }: { current: string; next: string }) =>
      settingsApi.changePassword(current, next),
    onSuccess: () => { toast('Password changed successfully', 'success'); setCurrentPwd(''); setNewPwd(''); setConfirmPwd('') },
    onError: (err: any) => toast(err?.response?.data?.detail || 'Password change failed', 'error'),
  })

  const revokeSessionMut = useMutation({
    mutationFn: (id: string) => settingsApi.revokeSession(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['settings-sessions'] }); toast('Session revoked', 'success') },
  })

  const revokeAllMut = useMutation({
    mutationFn: () => settingsApi.revokeAllSessions(),
    onSuccess: () => { logout(); navigate('/login') },
  })

  const deleteAccountMut = useMutation({
    mutationFn: (pwd: string) => settingsApi.deleteAccount(pwd),
    onSuccess: () => { logout(); navigate('/') },
    onError: (err: any) => toast(err?.response?.data?.detail || 'Account deletion failed', 'error'),
  })

  // Form state
  const [displayName, setDisplayName] = useState('')
  const [currentPwd, setCurrentPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [deletePwd, setDeletePwd] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const navItems: { id: Section; label: string; icon: React.ReactNode }[] = [
    { id: 'account', label: 'Account', icon: <User size={16} /> },
    { id: 'password', label: 'Password', icon: <Lock size={16} /> },
    { id: 'sessions', label: 'Active Sessions', icon: <Monitor size={16} /> },
    { id: 'privacy', label: 'Data & Privacy', icon: <Shield size={16} /> },
    { id: 'danger', label: 'Danger Zone', icon: <Trash2 size={16} /> },
  ]

  return (
    <AppLayout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Settings & Privacy</h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginTop: 4 }}>
            Manage your account, security and data preferences.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 24, alignItems: 'start' }}>
          {/* Sidebar */}
          <Card style={{ padding: '8px' }}>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {navItems.map(({ id, label, icon }) => (
                <button
                  key={id}
                  id={`settings-nav-${id}`}
                  onClick={() => setActiveSection(id)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '9px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
                    fontSize: '0.875rem', fontWeight: activeSection === id ? 600 : 400,
                    background: activeSection === id ? 'rgba(99,102,241,0.12)' : 'transparent',
                    color: activeSection === id ? 'var(--brand)' : (id === 'danger' ? '#ef4444' : 'var(--text)'),
                    transition: 'background 0.15s',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>{icon}{label}</span>
                  {activeSection === id && <ChevronRight size={14} />}
                </button>
              ))}
            </nav>
          </Card>

          {/* Content */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Account */}
            {activeSection === 'account' && (
              <Card>
                <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 20 }}>Account Information</h2>
                {isLoading ? (
                  <p style={{ color: 'var(--muted)', fontSize: '0.875rem' }}>Loading…</p>
                ) : (
                  <>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                      {[
                        { label: 'Email', value: account?.email },
                        { label: 'Joined', value: account?.created_at ? new Date(account.created_at).toLocaleDateString() : '—' },
                        { label: 'Email Verified', value: account?.email_verified ? '✓ Verified' : '✗ Not verified' },
                        { label: 'Setup Complete', value: account?.setup_complete ? '✓ Yes' : '✗ No' },
                      ].map(({ label, value }) => (
                        <div key={label}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: 4 }}>{label}</div>
                          <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{value}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ borderTop: '1px solid var(--line)', paddingTop: 20 }}>
                      <label style={{ fontSize: '0.875rem', fontWeight: 500, display: 'block', marginBottom: 8 }}>Display Name</label>
                      <div style={{ display: 'flex', gap: 12 }}>
                        <input
                          id="settings-display-name"
                          className="input-field"
                          value={displayName || account?.full_name || ''}
                          onChange={e => setDisplayName(e.target.value)}
                          placeholder="Your display name"
                          style={{ flex: 1 }}
                        />
                        <Button
                          id="settings-save-name"
                          size="sm"
                          isLoading={updateNameMut.isPending}
                          onClick={() => updateNameMut.mutate(displayName || account?.full_name || '')}
                        >
                          Save
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </Card>
            )}

            {/* Password */}
            {activeSection === 'password' && (
              <Card>
                <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 20 }}>Change Password</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {[
                    { id: 'current-password', label: 'Current Password', value: currentPwd, setter: setCurrentPwd },
                    { id: 'new-password', label: 'New Password (min 8 chars)', value: newPwd, setter: setNewPwd },
                    { id: 'confirm-password', label: 'Confirm New Password', value: confirmPwd, setter: setConfirmPwd },
                  ].map(({ id, label, value, setter }) => (
                    <div key={id}>
                      <label style={{ fontSize: '0.875rem', fontWeight: 500, display: 'block', marginBottom: 6 }}>{label}</label>
                      <input
                        id={`settings-${id}`}
                        type="password"
                        className="input-field"
                        value={value}
                        onChange={e => setter(e.target.value)}
                      />
                    </div>
                  ))}
                  {newPwd && confirmPwd && newPwd !== confirmPwd && (
                    <p style={{ fontSize: '0.8rem', color: '#f87171' }}>Passwords do not match</p>
                  )}
                  <Button
                    id="settings-change-password"
                    isLoading={changePasswordMut.isPending}
                    disabled={!currentPwd || !newPwd || newPwd !== confirmPwd || newPwd.length < 8}
                    onClick={() => changePasswordMut.mutate({ current: currentPwd, next: newPwd })}
                  >
                    Change Password
                  </Button>
                </div>
              </Card>
            )}

            {/* Sessions */}
            {activeSection === 'sessions' && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Active Sessions</h2>
                  <Button
                    id="settings-revoke-all"
                    variant="outline"
                    size="sm"
                    isLoading={revokeAllMut.isPending}
                    onClick={() => revokeAllMut.mutate()}
                  >
                    <LogOut size={14} /> Sign Out Everywhere
                  </Button>
                </div>
                {sessions.length === 0 ? (
                  <p style={{ color: 'var(--muted)', fontSize: '0.875rem' }}>No active sessions found.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {sessions.map((s: any) => (
                      <div key={s.session_id} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '12px 14px', background: 'var(--bg)', border: '1px solid var(--line)',
                        borderRadius: 8,
                      }}>
                        <div>
                          <div style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: 2 }}>Session</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                            Created: {s.created_at ? new Date(s.created_at).toLocaleString() : '—'}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                            Expires: {s.expires_at ? new Date(s.expires_at).toLocaleDateString() : '—'}
                          </div>
                        </div>
                        <Button
                          id={`revoke-session-${s.session_id}`}
                          variant="outline"
                          size="sm"
                          onClick={() => revokeSessionMut.mutate(s.session_id)}
                        >
                          Revoke
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {/* Privacy */}
            {activeSection === 'privacy' && (
              <Card>
                <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 20 }}>Data & Privacy</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div style={{
                    padding: '16px', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 10,
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6 }}>Export Your Data</div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: 14, lineHeight: 1.5 }}>
                      Download a full JSON export of your profile, education, experience, skills, documents and application history.
                    </p>
                    <Button
                      id="settings-export-data"
                      variant="outline"
                      size="sm"
                      leftIcon={<Download size={14} />}
                      onClick={async () => {
                        try {
                          const res = await settingsApi.exportData()
                          const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url; a.download = 'formpilot-export.json'; a.click()
                          URL.revokeObjectURL(url)
                          addToast('Data exported!', 'success')
                        } catch {
                          addToast('Export failed', 'error')
                        }
                      }}
                    >
                      Download JSON Export
                    </Button>
                  </div>

                  <div style={{
                    padding: '16px', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 10,
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6 }}>What FormPilot Stores</div>
                    <ul style={{ fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.8, paddingLeft: 16 }}>
                      <li>Profile data you explicitly provide</li>
                      <li>Application session logs (no form credentials)</li>
                      <li>Documents you upload (stored locally)</li>
                      <li>Answers you choose to save to your profile</li>
                    </ul>
                  </div>

                  <div style={{
                    padding: '16px', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 10,
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6 }}>What FormPilot Never Stores</div>
                    <ul style={{ fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.8, paddingLeft: 16 }}>
                      <li>Passwords to external websites</li>
                      <li>OTPs, authentication tokens</li>
                      <li>Payment or banking information</li>
                      <li>Aadhaar, PAN or government identity numbers</li>
                    </ul>
                  </div>
                </div>
              </Card>
            )}

            {/* Danger Zone */}
            {activeSection === 'danger' && (
              <Card style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <AlertTriangle size={18} color="#ef4444" />
                  <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#ef4444' }}>Danger Zone</h2>
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: 20, lineHeight: 1.6 }}>
                  Permanently delete your account and all associated data including profile, documents and application history. 
                  <strong style={{ color: 'var(--text)' }}> This action cannot be undone.</strong>
                </p>
                {!showDeleteConfirm ? (
                  <Button
                    id="settings-delete-account-btn"
                    variant="outline"
                    style={{ borderColor: '#ef4444', color: '#ef4444' }}
                    onClick={() => setShowDeleteConfirm(true)}
                  >
                    <Trash2 size={16} /> Delete My Account
                  </Button>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{
                      padding: '14px', background: 'rgba(239,68,68,0.06)',
                      border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10,
                      fontSize: '0.875rem', color: '#fca5a5',
                    }}>
                      ⚠️ Enter your password to confirm permanent account deletion.
                    </div>
                    <input
                      id="settings-delete-password"
                      type="password"
                      className="input-field"
                      value={deletePwd}
                      onChange={e => setDeletePwd(e.target.value)}
                      placeholder="Your account password"
                      style={{ borderColor: '#ef4444' }}
                    />
                    <div style={{ display: 'flex', gap: 12 }}>
                      <Button
                        id="settings-cancel-delete"
                        variant="outline"
                        onClick={() => { setShowDeleteConfirm(false); setDeletePwd('') }}
                      >
                        Cancel
                      </Button>
                      <Button
                        id="settings-confirm-delete"
                        isLoading={deleteAccountMut.isPending}
                        disabled={!deletePwd}
                        style={{ background: '#ef4444', border: 'none' }}
                        onClick={() => deleteAccountMut.mutate(deletePwd)}
                      >
                        Permanently Delete Account
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
