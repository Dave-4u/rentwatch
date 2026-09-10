import { useEffect, useState } from 'react'
import { api, type User } from '../api/client'
import { useAuth } from '../auth'

export default function Approvals() {
  const { user, loading: authLoading } = useAuth()
  const [pending, setPending] = useState<User[]>([])
  const [accounts, setAccounts] = useState<User[]>([])
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load() {
    try {
      setError('')
      const [p, a] = await Promise.all([api.pendingUsers(), api.users()])
      setPending(p)
      setAccounts(a)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    }
  }

  useEffect(() => {
    if (authLoading || !user) return
    if (user.role === 'tenant') return
    load()
  }, [authLoading, user?.id, user?.role])

  if (user?.role === 'tenant') {
    return <div className="error">Staff only</div>
  }

  async function act(id: number, action: 'approve' | 'reject' | 'suspend') {
    setError('')
    setMsg('')
    try {
      if (action === 'approve') await api.approveUser(id)
      if (action === 'reject') await api.rejectUser(id)
      if (action === 'suspend') await api.suspendUser(id)
      setMsg(`User ${action}d.`)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Action failed')
    }
  }

  async function removeAccount(u: User) {
    const who = `${u.full_name} (${u.role})`
    if (!window.confirm(`Delete ${who}? Active leases will be ended. This cannot be undone.`)) {
      return
    }
    setError('')
    setMsg('')
    try {
      await api.deleteUser(u.id)
      setMsg(`${u.full_name} deleted.`)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  const canDelete = (u: User) => {
    if (!user) return false
    if (u.id === user.id) return false
    if (u.role === 'landlord') return false
    if (u.role === 'agent') return user.role === 'landlord'
    if (u.role === 'tenant') return user.role === 'landlord' || user.role === 'agent'
    return false
  }

  return (
    <div>
      <h1 className="page-title">Approvals</h1>
      <p className="muted">Approve or reject agents and tenants waiting for access.</p>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}
      {pending.length === 0 && <p className="empty">No pending users.</p>}
      {pending.map((u) => (
        <div className="card" key={u.id}>
          <h3>{u.full_name}</h3>
          <div className="muted">
            {u.email} · {u.phone || 'no phone'}
          </div>
          <div className="row" style={{ marginTop: '0.5rem' }}>
            <span className="badge pending">{u.role}</span>
            <span className="badge warn">{u.status}</span>
          </div>
          <div className="stack-actions">
            <button className="btn sm" type="button" onClick={() => act(u.id, 'approve')}>
              Approve
            </button>
            <button className="btn sm secondary" type="button" onClick={() => act(u.id, 'reject')}>
              Reject
            </button>
            <button className="btn sm danger" type="button" onClick={() => act(u.id, 'suspend')}>
              Suspend
            </button>
          </div>
        </div>
      ))}

      <h2 className="page-title" style={{ marginTop: '1.5rem', fontSize: '1.15rem' }}>
        Accounts
      </h2>
      <p className="muted">
        {user?.role === 'landlord'
          ? 'Delete tenants or agents. Active leases are ended first.'
          : 'Delete tenant accounts. Active leases are ended first.'}
      </p>
      {accounts.length === 0 && <p className="empty">No accounts to manage.</p>}
      {accounts.map((u) => (
        <div className="card" key={`acc-${u.id}`}>
          <h3>{u.full_name}</h3>
          <div className="muted">
            {u.email} · {u.phone || 'no phone'}
          </div>
          <div className="row" style={{ marginTop: '0.5rem' }}>
            <span className="badge pending">{u.role}</span>
            <span className="badge ok">{u.status}</span>
          </div>
          {canDelete(u) && (
            <div className="stack-actions">
              <button className="btn sm danger" type="button" onClick={() => removeAccount(u)}>
                Delete
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
