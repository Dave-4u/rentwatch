import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const staff = user?.role === 'landlord' || user?.role === 'agent'

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand" style={{ color: '#fff' }}>
          RentWatch
        </Link>
        <div className="topbar-actions">
          <Link to="/notifications">Alerts</Link>
          <button
            className="linkish"
            type="button"
            onClick={() => {
              logout()
              nav('/login')
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <nav className="bottom-nav">
        <NavLink to="/" end>
          <span className="ico">⌂</span>Home
        </NavLink>
        <NavLink to="/properties">
          <span className="ico">▣</span>Properties
        </NavLink>
        <NavLink to="/leases">
          <span className="ico">☰</span>Leases
        </NavLink>
        {staff ? (
          <NavLink to="/payments/new">
            <span className="ico">₦</span>Pay
          </NavLink>
        ) : (
          <NavLink to="/notifications">
            <span className="ico">🔔</span>Alerts
          </NavLink>
        )}
        {staff && (
          <NavLink to="/approvals">
            <span className="ico">✓</span>Approvals
          </NavLink>
        )}
      </nav>
    </div>
  )
}
