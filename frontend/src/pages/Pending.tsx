import { useAuth } from '../auth'

export default function Pending() {
  const { user, logout, refresh } = useAuth()
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Awaiting approval</h1>
        <p>
          Hi {user?.full_name}. Your <strong>{user?.role}</strong> account is{' '}
          <span className="badge pending">{user?.status}</span>.
        </p>
        <p className="muted">
          The landlord or an approved agent must approve your account before you can open dashboards.
        </p>
        <div className="stack-actions">
          <button className="btn" type="button" onClick={() => refresh()}>
            Check again
          </button>
          <button className="btn secondary" type="button" onClick={() => logout()}>
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
