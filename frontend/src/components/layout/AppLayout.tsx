import { NavLink, useNavigate } from 'react'
import {
  Bot, LayoutDashboard, User, FileText, History, LogOut,
  Zap, Settings
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'
import { useToast } from '@/components/ui/Toast'
import { getInitials } from '@/utils/cn'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profile', icon: User, label: 'Profile' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/applications', icon: History, label: 'Applications' },
]

export function AppLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const { user, refreshToken, logout } = useAuthStore()
  const { toast } = useToast()

  const handleLogout = async () => {
    try { if (refreshToken) await authApi.logout(refreshToken) } catch {}
    logout()
    navigate('/login', { replace: true })
    toast('Signed out successfully', 'success')
  }

  return (
    <div className="app-layout">
      {/* Topbar matching wireframes */}
      <header className="topbar">
        <div className="topbar-logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/dashboard')}>
          <div className="topbar-logo-icon">
            <Bot size={20} />
          </div>
          <span>FORMPILOT AI</span>
        </div>
        <div className="topbar-right">
          <span className="tag tag-success">Profile Active</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: 'var(--brand-light)',
                border: '1px solid var(--line)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 700,
                color: 'var(--brand)'
              }}
            >
              {user ? getInitials(user.full_name) : 'U'}
            </div>
            <button
              onClick={handleLogout}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: '4px' }}
              title="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container: Sidebar + Content */}
      <div className="app-container">
        <aside className="sidebar-app">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `item ${isActive ? 'sel' : ''}`}
            >
              {label}
            </NavLink>
          ))}
          <div
            className="item"
            style={{ marginTop: 'auto', cursor: 'pointer' }}
            onClick={handleLogout}
          >
            Sign out
          </div>
        </aside>

        <main className="main-content animate-slide-up">
          {children}
        </main>
      </div>
    </div>
  )
}
