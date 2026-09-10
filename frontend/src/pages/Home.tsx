import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, formatNgn, type Lease, type Payment } from '../api/client'
import { useAuth } from '../auth'

export default function Home() {
  const { user } = useAuth()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        let d: Record<string, unknown>
        if (user?.role === 'landlord') d = await api.dashboardLandlord()
        else if (user?.role === 'agent') d = await api.dashboardAgent()
        else d = await api.dashboardTenant()
        if (!cancelled) setData(d)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load')
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [user?.role])

  if (error) return <div className="error">{error}</div>
  if (!data) return <p className="muted">Loading dashboard…</p>

  if (user?.role === 'tenant') {
    const leases = (data.leases as Lease[]) || []
    const payments = (data.recent_payments as Payment[]) || []
    return (
      <div>
        <h1 className="page-title">Welcome, {user.full_name}</h1>
        <div className="grid stats">
          <div className="card stat">
            <div className="num">{leases.filter((l) => l.status === 'active').length}</div>
            <div className="muted">Active leases</div>
          </div>
          <div className="card stat">
            <div className="num">{formatNgn(data.total_balance_due as number)}</div>
            <div className="muted">Balance due</div>
          </div>
        </div>
        <div className="card">
          <h2>My leases</h2>
          {leases.length === 0 && (
            <p className="empty">
              No property assigned yet — wait for your landlord/agent.
            </p>
          )}
          {leases.map((l) => (
            <div className="list-item" key={l.id}>
              <div>
                <strong>{l.property_name || `Property #${l.property_id}`}</strong>
                <div className="muted">
                  Rent {formatNgn(l.rent_amount)} · {l.billing_period === 'monthly' ? 'monthly' : 'yearly'} · due {l.due_date || '—'} · {l.current_period}
                </div>
              </div>
              <div>
                {l.is_overdue ? (
                  <span className="badge overdue">Overdue</span>
                ) : (
                  <span className="badge ok">OK</span>
                )}
                <div className="muted">{formatNgn(l.balance_due)}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="card">
          <h2>Payment history</h2>
          {payments.length === 0 && <p className="empty">No payments recorded.</p>}
          {payments.map((p) => (
            <div className="list-item" key={p.id}>
              <div>
                <strong>{formatNgn(p.amount)}</strong>
                <div className="muted">
                  {p.paid_on} · {p.method} · period {p.period_key}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const overdue = (data.overdue_leases as Lease[]) || []
  const payments = (data.recent_payments as Payment[]) || []

  return (
    <div>
      <h1 className="page-title">
        {user?.role === 'landlord' ? 'Landlord' : 'Agent'} dashboard
      </h1>
      <div className="grid stats">
        <div className="card stat">
          <div className="num">{String(data.property_count)}</div>
          <div className="muted">Properties</div>
        </div>
        <div className="card stat">
          <div className="num">{String(data.active_leases)}</div>
          <div className="muted">Active leases</div>
        </div>
        <div className="card stat">
          <div className="num">{String(data.overdue_count)}</div>
          <div className="muted">Overdue</div>
        </div>
        <div className="card stat">
          <div className="num">{String(data.pending_users)}</div>
          <div className="muted">Pending users</div>
        </div>
      </div>
      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h2>Overdue rents</h2>
          <Link to="/payments/new" className="btn sm">
            Record payment
          </Link>
        </div>
        {overdue.length === 0 && <p className="empty">No overdue leases.</p>}
        {overdue.map((l) => (
          <div className="list-item" key={l.id}>
            <div>
              <strong>{l.property_name}</strong>
              <div className="muted">
                {l.tenant_name} · {formatNgn(l.balance_due)} due
              </div>
            </div>
            <span className="badge overdue">Overdue</span>
          </div>
        ))}
      </div>
      <div className="card">
        <h2>Recent payments</h2>
        {payments.length === 0 && <p className="empty">No payments yet.</p>}
        {payments.map((p) => (
          <div className="list-item" key={p.id}>
            <div>
              <strong>{formatNgn(p.amount)}</strong>
              <div className="muted">
                Lease #{p.lease_id} · {p.paid_on} · {p.method}
              </div>
            </div>
          </div>
        ))}
      </div>
      {(data.pending_users as number) > 0 && (
        <p>
          <Link to="/approvals">Review {String(data.pending_users)} pending approval(s)</Link>
        </p>
      )}
    </div>
  )
}
