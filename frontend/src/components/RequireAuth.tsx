import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <div className="main"><p className="muted">Loading…</p></div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc }} />
  if (user.status !== 'approved' && loc.pathname !== '/pending') {
    return <Navigate to="/pending" replace />
  }
  if (user.status === 'approved' && loc.pathname === '/pending') {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
