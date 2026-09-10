import { type FormEvent, useEffect, useState } from 'react'
import { api, formatNgn, type Lease, type Property } from '../api/client'
import { useAuth } from '../auth'

export default function Leases() {
  const { user, loading: authLoading } = useAuth()
  const staff = user?.role === 'landlord' || user?.role === 'agent'
  const [leases, setLeases] = useState<Lease[]>([])
  const [props, setProps] = useState<Property[]>([])
  const [tenants, setTenants] = useState<{ id: number; full_name: string; email: string }[]>([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useState({
    property_id: '',
    tenant_id: '',
    rent_amount: '',
    due_date: today,
    start_date: today,
    billing_period: 'yearly',
  })

  async function load() {
    try {
      setError('')
      setLeases(await api.leases())
      if (user?.role === 'landlord' || user?.role === 'agent') {
        const [propertyList, tenantList] = await Promise.all([
          api.properties(),
          api.tenantsForLease(),
        ])
        setProps(propertyList)
        setTenants(tenantList)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    }
  }

  useEffect(() => {
    if (authLoading || !user) return
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, user?.id, user?.role])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    try {
      await api.createLease({
        property_id: Number(form.property_id),
        tenant_id: Number(form.tenant_id),
        rent_amount: Number(form.rent_amount),
        due_date: form.due_date,
        start_date: form.start_date,
        billing_period: form.billing_period,
        status: 'active',
      })
      setShowForm(false)
      setForm({
        property_id: '',
        tenant_id: '',
        rent_amount: '',
        due_date: today,
        start_date: today,
        billing_period: 'yearly',
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    }
  }

  async function endLease(id: number) {
    try {
      await api.updateLease(id, { status: 'ended' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  return (
    <div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1 className="page-title">Leases</h1>
        {staff && (
          <button className="btn sm" type="button" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : 'New lease'}
          </button>
        )}
      </div>
      {error && <div className="error">{error}</div>}
      {showForm && staff && (
        <div className="card">
          <h2>Create lease</h2>
          <form className="form" onSubmit={onCreate}>
            <label>
              Property
              <select
                value={form.property_id}
                onChange={(e) => setForm({ ...form, property_id: e.target.value })}
                required
              >
                <option value="">Select property…</option>
                {props.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.property_type})
                  </option>
                ))}
              </select>
            </label>
            {props.length === 0 && (
              <p className="empty">No properties yet. Create a property first.</p>
            )}
            <label>
              Tenant
              <select
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
                required
              >
                <option value="">Select tenant…</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name} ({t.email})
                  </option>
                ))}
              </select>
            </label>
            {tenants.length === 0 && (
              <p className="empty">
                No approved tenants yet. Approve a tenant under Approvals, then assign them here.
              </p>
            )}
            <label>
              Rent amount (NGN / year)
              <input
                type="number"
                min={1}
                value={form.rent_amount}
                onChange={(e) => setForm({ ...form, rent_amount: e.target.value })}
                required
              />
            </label>
            <label>
              Billing period
              <select
                value={form.billing_period}
                onChange={(e) => setForm({ ...form, billing_period: e.target.value })}
              >
                <option value="yearly">Yearly</option>
                <option value="monthly">Monthly</option>
              </select>
            </label>
            <label>
              Due date
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                required
              />
            </label>
            <label>
              Start date
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                required
              />
            </label>
            <button className="btn" type="submit" disabled={!tenants.length || !props.length}>
              Save lease
            </button>
          </form>
        </div>
      )}
      {leases.length === 0 && <p className="empty">No leases.</p>}
      {leases.map((l) => (
        <div className="card" key={l.id}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h3>
              {l.property_name || `Property #${l.property_id}`}
              {l.property_type ? ` · ${l.property_type}` : ''}
            </h3>
            {l.is_overdue ? (
              <span className="badge overdue">Overdue</span>
            ) : l.status === 'active' ? (
              <span className="badge ok">Active</span>
            ) : (
              <span className="badge warn">Ended</span>
            )}
          </div>
          <div className="muted">
            Tenant: {l.tenant_name || l.tenant_id} · Rent {formatNgn(l.rent_amount)} ·{' '}
            {l.billing_period === 'monthly' ? 'Monthly' : 'Yearly'} · Due {l.due_date || '—'}
          </div>
          <div className="muted">
            Period {l.current_period} · Balance {formatNgn(l.balance_due)} · Started {l.start_date}
          </div>
          {staff && l.status === 'active' && (
            <div className="stack-actions">
              <button className="btn sm secondary" type="button" onClick={() => endLease(l.id)}>
                End lease
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
