import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  Zap, Shield, Brain, Search, FileText, CheckCircle2,
  ArrowRight, Lock, Users, Globe
} from 'lucide-react'

const TAGLINES = [
  'Find and fill the TCS Agentic AI Engineer application.',
  'Complete the Google internship form for me.',
  'Open this Greenhouse link and fill it with my profile.',
  'Apply to remote Python roles in Bangalore.',
]

const FEATURES = [
  {
    icon: <Search size={20} />,
    title: 'Intelligent Discovery',
    desc: 'Searches DuckDuckGo for official career pages and trusted ATS portals — ranked by domain trust and intent relevance.',
  },
  {
    icon: <Brain size={20} />,
    title: 'AI Field Mapping',
    desc: 'Semantic understanding maps unusual field labels to your profile automatically, with confidence scoring.',
  },
  {
    icon: <FileText size={20} />,
    title: 'Profile Vault',
    desc: 'Store education, experience, skills, projects, certifications and documents — reused across every application.',
  },
  {
    icon: <Shield size={20} />,
    title: 'Privacy by Design',
    desc: 'Only the profile sections actually needed by the form are loaded into agent memory. Your data stays yours.',
  },
  {
    icon: <Users size={20} />,
    title: 'Multi-Platform Support',
    desc: 'Native adapters for Greenhouse, Lever, Workday, and more — with rule-based fallback for any other portal.',
  },
  {
    icon: <Globe size={20} />,
    title: 'Universal Forms',
    desc: 'Job applications, university admissions, government portals — if it has a form, FormPilot can understand it.',
  },
]

const STEPS = [
  { num: '01', title: 'Describe your goal', desc: 'Type a natural language request or paste a direct URL.' },
  { num: '02', title: 'AI searches & maps', desc: 'Agents find the form, extract every field, and map your profile.' },
  { num: '03', title: 'You review & submit', desc: 'You check every filled value and submit on your own terms.' },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const [taglineIdx, setTaglineIdx] = useState(0)
  const [displayed, setDisplayed] = useState('')
  const [isTyping, setIsTyping] = useState(true)

  useEffect(() => {
    const target = TAGLINES[taglineIdx]
    let i = 0
    setDisplayed('')
    setIsTyping(true)
    const interval = setInterval(() => {
      i++
      setDisplayed(target.slice(0, i))
      if (i >= target.length) {
        clearInterval(interval)
        setIsTyping(false)
        setTimeout(() => {
          setTaglineIdx(prev => (prev + 1) % TAGLINES.length)
        }, 2800)
      }
    }, 38)
    return () => clearInterval(interval)
  }, [taglineIdx])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', fontFamily: 'inherit' }}>

      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <nav style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '16px 48px', borderBottom: '1px solid var(--line)',
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(244, 242, 235, 0.92)', backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--brand)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={16} color="#fffef8" />
          </div>
          <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text)', letterSpacing: '0.01em' }}>FormPilot AI</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            id="nav-sign-in"
            onClick={() => navigate('/login')}
            style={{
              background: 'transparent', border: '1px solid var(--line)',
              color: 'var(--muted)', padding: '8px 18px', borderRadius: 8,
              cursor: 'pointer', fontSize: '0.875rem', fontWeight: 500,
              transition: 'all 0.18s',
            }}
            onMouseEnter={e => { (e.currentTarget).style.color = 'var(--text)'; (e.currentTarget).style.borderColor = 'var(--brand)' }}
            onMouseLeave={e => { (e.currentTarget).style.color = 'var(--muted)'; (e.currentTarget).style.borderColor = 'var(--line)' }}
          >
            Sign In
          </button>
          <button
            id="nav-get-started"
            onClick={() => navigate('/register')}
            className="btn-brand"
            style={{ fontSize: '0.875rem', padding: '8px 18px', borderRadius: 8 }}
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section style={{
        textAlign: 'center',
        padding: '96px 24px 80px',
        background: 'radial-gradient(ellipse 70% 55% at 50% 0%, rgba(29,92,122,0.07) 0%, transparent 68%)',
      }}>
        <h1 style={{
          fontSize: 'clamp(2rem, 5vw, 3.2rem)',
          fontWeight: 800, lineHeight: 1.15,
          color: 'var(--text)', marginBottom: 20,
          letterSpacing: '-0.02em',
        }}>
          Stop filling forms.<br />
          <span style={{ color: 'var(--brand)' }}>Let the AI do it.</span>
        </h1>
        <p style={{
          fontSize: 'clamp(1rem, 2vw, 1.18rem)',
          color: 'var(--muted)', maxWidth: 560, margin: '0 auto 40px',
          lineHeight: 1.65,
        }}>
          FormPilot AI discovers the form, maps every field to your profile,
          and fills it — you stay in control of submission.
        </p>

        {/* Typewriter demo box */}
        <div style={{
          maxWidth: 580, margin: '0 auto 48px',
          background: 'var(--panel-strong)',
          border: '1px solid var(--line)',
          borderRadius: 12,
          padding: '18px 20px',
          textAlign: 'left',
          boxShadow: 'var(--shadow)',
        }}>
          <div style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10 }}>
            Try saying
          </div>
          <div style={{ fontSize: '1rem', color: 'var(--text)', minHeight: '1.5em', fontStyle: 'italic' }}>
            {displayed}
            <span style={{
              display: 'inline-block', width: 2, height: '1em',
              background: isTyping ? 'var(--brand)' : 'transparent',
              marginLeft: 2, verticalAlign: 'text-bottom',
              animation: isTyping ? 'none' : 'blink 0.9s step-end infinite',
            }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            id="hero-start"
            onClick={() => navigate('/register')}
            className="btn-brand"
            style={{ fontSize: '1rem', padding: '12px 28px', borderRadius: 10, display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            Start for free <ArrowRight size={16} />
          </button>
          <button
            id="hero-login"
            onClick={() => navigate('/login')}
            className="btn-ghost"
            style={{ fontSize: '1rem', padding: '12px 28px', borderRadius: 10, border: '1px solid var(--line)' }}
          >
            Sign in to continue
          </button>
        </div>
      </section>

      {/* ── Trust bar ──────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: 40, flexWrap: 'wrap',
        padding: '24px 48px', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
        background: 'rgba(255,255,255,0.5)',
      }}>
        {['Greenhouse', 'Lever', 'Workday', 'Taleo', 'iCIMS', 'SmartRecruiters'].map(ats => (
          <span key={ats} style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            {ats}
          </span>
        ))}
      </div>

      {/* ── How it works ───────────────────────────────────────────────── */}
      <section style={{ padding: '80px 48px', maxWidth: 900, margin: '0 auto' }}>
        <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10, textAlign: 'center' }}>
          HOW IT WORKS
        </p>
        <h2 style={{ fontSize: 'clamp(1.5rem, 3vw, 2.2rem)', fontWeight: 700, textAlign: 'center', color: 'var(--text)', marginBottom: 56 }}>
          Three steps to a completed application
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 24 }}>
          {STEPS.map(step => (
            <div key={step.num} className="glass-card" style={{ padding: '28px 24px' }}>
              <div style={{
                fontSize: '2rem', fontWeight: 800, color: 'var(--brand)',
                opacity: 0.25, lineHeight: 1, marginBottom: 16, fontVariantNumeric: 'tabular-nums',
              }}>
                {step.num}
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
                {step.title}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)', lineHeight: 1.6 }}>
                {step.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────────────────── */}
      <section style={{ padding: '60px 48px 80px', background: 'rgba(255,255,255,0.45)', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10, textAlign: 'center' }}>
            CAPABILITIES
          </p>
          <h2 style={{ fontSize: 'clamp(1.5rem, 3vw, 2.2rem)', fontWeight: 700, textAlign: 'center', color: 'var(--text)', marginBottom: 48 }}>
            Everything you need to fill forms faster
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
            {FEATURES.map(f => (
              <div
                key={f.title}
                className="glass-card-hover"
                style={{ padding: '24px 22px' }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: 'var(--brand-light)', color: 'var(--brand)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 14,
                }}>
                  {f.icon}
                </div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text)', marginBottom: 6 }}>
                  {f.title}
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--muted)', lineHeight: 1.65 }}>
                  {f.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Safety Promise ─────────────────────────────────────────────── */}
      <section style={{ padding: '80px 48px', maxWidth: 760, margin: '0 auto', textAlign: 'center' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '7px 16px', borderRadius: 8,
          background: 'rgba(47, 111, 79, 0.08)',
          border: '1px solid rgba(47, 111, 79, 0.2)',
          color: 'var(--green)', fontWeight: 600, fontSize: '0.82rem',
          textTransform: 'uppercase', letterSpacing: '0.08em',
          marginBottom: 20,
        }}>
          <Lock size={13} /> Safety Promise
        </div>
        <h2 style={{ fontSize: 'clamp(1.4rem, 3vw, 2rem)', fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
          You are always in control
        </h2>
        <p style={{ fontSize: '1rem', color: 'var(--muted)', lineHeight: 1.7, marginBottom: 32 }}>
          FormPilot AI will <strong>never</strong> submit a form on your behalf. Sensitive fields 
          (OTP, Aadhaar, PAN, bank details, CAPTCHA) are always flagged for manual handling.
          Your documents and identity data never leave your device without your explicit approval.
        </p>
        <div style={{ display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap' }}>
          {['Never auto-submits', 'HITL on every review', 'Sensitive fields protected', 'Data stays yours'].map(promise => (
            <div key={promise} style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: '0.875rem', color: 'var(--text)', fontWeight: 500 }}>
              <CheckCircle2 size={15} color="var(--green)" />
              {promise}
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────── */}
      <section style={{
        padding: '60px 48px 80px',
        background: 'var(--brand)',
        textAlign: 'center',
      }}>
        <h2 style={{ fontSize: 'clamp(1.5rem, 3vw, 2.2rem)', fontWeight: 700, color: '#fffef8', marginBottom: 12 }}>
          Ready to stop filling forms manually?
        </h2>
        <p style={{ fontSize: '1rem', color: 'rgba(255,254,248,0.75)', marginBottom: 32 }}>
          Set up your profile once. FormPilot handles the rest.
        </p>
        <button
          id="cta-register"
          onClick={() => navigate('/register')}
          style={{
            background: '#fffef8', color: 'var(--brand)',
            border: 'none', padding: '13px 32px', borderRadius: 10,
            fontSize: '1rem', fontWeight: 700, cursor: 'pointer',
            transition: 'opacity 0.18s',
            display: 'inline-flex', alignItems: 'center', gap: 8,
          }}
          onMouseEnter={e => { (e.currentTarget).style.opacity = '0.9' }}
          onMouseLeave={e => { (e.currentTarget).style.opacity = '1' }}
        >
          Create free account <ArrowRight size={16} />
        </button>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer style={{
        padding: '28px 48px',
        borderTop: '1px solid var(--line)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 12,
        background: 'var(--panel-strong)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 24, height: 24, borderRadius: 6, background: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={12} color="#fffef8" />
          </div>
          <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text)' }}>FormPilot AI</span>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
          © {new Date().getFullYear()} FormPilot AI. Built with LangGraph · Playwright · FastAPI.
        </span>
      </footer>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  )
}
