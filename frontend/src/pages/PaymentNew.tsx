import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, formatNgn, leaseLabel, type Lease } from '../api/client'
import { useAuth } from '../auth'

export default function PaymentNew() {
  const { user, loading: authLoading } = useAuth()
  const nav = useNavigate()
  const [leases, setLeases] = useState<Lease[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [form, setForm] = useState({
    lease_id: '',
    amount: '',
    paid_on: new Date().toISOString().slice(0, 10),
    method: 'cash',
    note: '',
    period_key: new Date().toISOString().slice(0, 7),
  })

  useEffect(() => {
    if (authLoading) return
    if (!user) return
    if (user.role === 'tenant') {
      nav('/')
      return
    }
    setLoaded(false)
    api
      .activeLeasesForPayment()
      .then((ls) => setLeases(ls))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed'))
      .finally(() => setLoaded(true))
  }, [user, authLoading, nav])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setOk('')
    try {
      await api.createPayment({
        lease_id: Number(form.lease_id),
        amount: Number(form.amount),
        paid_on: form.paid_on,
        method: form.method,
        note: form.note || undefined,
        period_key: form.period_key,
      })
      setOk('Payment recorded.')
      setForm({
        ...form,
        amount: '',
        note: '',
      })
      const refreshed = await api.activeLeasesForPayment()
      setLeases(refreshed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record payment')
    }
  }

  const selected = leases.find((l) => String(l.id) === form.lease_id)

  return (
    <div>
      <h1 className="page-title">Record payment</h1>
      <p className="muted">Physical payments only — cash, transfer, or other. No online checkout.</p>
      {error && <div className="error">{error}</div>}
      {ok && <div className="success">{ok}</div>}
      <div className="card">
        {loaded && leases.length === 0 ? (
          <div>
            <p className="empty">Create a lease first (assign a tenant to a property).</p>
            <p className="muted">
              Approve the tenant under Approvals, then create a lease on the{' '}
              <Link to="/leases">Leases</Link> page.
            </p>
          </div>
        ) : (
          <form className="form" onSubmit={onSubmit}>
            <label>
              Lease
              <select
                value={form.lease_id}
                onChange={(e) => {
                  const l = leases.find((x) => String(x.id) === e.target.value)
                  setForm({
                    ...form,
                    lease_id: e.target.value,
                    amount: l ? String(l.balance_due || l.rent_amount) : form.amount,
                  })
                }}
                required
              >
                <option value="">Select lease…</option>
                {leases.map((l) => (
                  <option key={l.id} value={l.id}>
                    {leaseLabel(l)}
                    {l.balance_due != null ? ` · ${formatNgn(l.balance_due)} due` : ''}
                  </option>
                ))}
              </select>
            </label>
            {selected && (
              <p className="muted">
                Rent {formatNgn(selected.rent_amount)} · period {selected.current_period} · due day{' '}
                {selected.due_day}
              </p>
            )}
            <label>
              Amount (NGN)
              <input
                type="number"
                min={1}
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
              />
            </label>
            <label>
              Paid on
              <input
                type="date"
                value={form.paid_on}
                onChange={(e) => setForm({ ...form, paid_on: e.target.value })}
                required
              />
            </label>
            <label>
              Period (YYYY-MM)
              <input
                value={form.period_key}
                onChange={(e) => setForm({ ...form, period_key: e.target.value })}
                pattern="\d{4}-\d{2}"
                required
              />
            </label>
            <label>
              Method
              <select
                value={form.method}
                onChange={(e) => setForm({ ...form, method: e.target.value })}
              >
                <option value="cash">Cash</option>
                <option value="transfer">Transfer</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Note
              <textarea
                rows={2}
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
              />
            </label>
            <button className="btn block" type="submit" disabled={!leases.length}>
              Save payment
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
