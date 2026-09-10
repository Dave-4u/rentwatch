import { type FormEvent, useEffect, useState } from 'react'
import { api, formatNgn, type Lease, type Property } from '../api/client'
import { useAuth } from '../auth'

export default function Leases() {
  const { user } = useAuth()
  const staff = user?.role === 'landlord' || user?.role === 'agent'
  const [leases, setLeases] = useState<Lease[]>([])
  const [props, setProps] = useState<Property[]>([])
  const [tenants, setTenants] = useState<{ id: number; full_name: string; email: string }[]>([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    property_id: '',
    tenant_id: '',
    rent_amount: '',
    due_day: '5',
    start_date: new Date().toISOString().slice(0, 10),
  })

  async function load() {
    try {
      setLeases(await api.leases())
      if (staff) {
        setProps(await api.properties())
        setTenants(await api.tenantsForLease())
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    try {
      await api.createLease({
        property_id: Number(form.property_id),
        tenant_id: Number(form.tenant_id),
        rent_amount: Number(form.rent_amount),
        due_day: Number(form.due_day),
        start_date: form.start_date,
        status: 'active',
      })
      setShowForm(false)
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
                <option value="">Select…</option>
                {props.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tenant
              <select
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
                required
              >
                <option value="">Select…</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name} ({t.email})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Rent amount (NGN)
              <input
                type="number"
                min={1}
                value={form.rent_amount}
                onChange={(e) => setForm({ ...form, rent_amount: e.target.value })}
                required
              />
            </label>
            <label>
              Due day (1–28)
              <input
                type="number"
                min={1}
                max={28}
                value={form.due_day}
                onChange={(e) => setForm({ ...form, due_day: e.target.value })}
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
            <button className="btn" type="submit">
              Save lease
            </button>
          </form>
        </div>
      )}
      {leases.length === 0 && <p className="empty">No leases.</p>}
      {leases.map((l) => (
        <div className="card" key={l.id}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h3>{l.property_name || `Property #${l.property_id}`}</h3>
            {l.is_overdue ? (
              <span className="badge overdue">Overdue</span>
            ) : l.status === 'active' ? (
              <span className="badge ok">Active</span>
            ) : (
              <span className="badge warn">Ended</span>
            )}
          </div>
          <div className="muted">
            Tenant: {l.tenant_name || l.tenant_id} · Rent {formatNgn(l.rent_amount)} · Due day{' '}
            {l.due_day}
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
