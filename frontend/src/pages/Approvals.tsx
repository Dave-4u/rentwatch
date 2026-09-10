import { useEffect, useState } from 'react'
import { api, type User } from '../api/client'
import { useAuth } from '../auth'

export default function Approvals() {
  const { user } = useAuth()
  const [items, setItems] = useState<User[]>([])
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load() {
    try {
      setItems(await api.pendingUsers())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    }
  }

  useEffect(() => {
    load()
  }, [])

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

  return (
    <div>
      <h1 className="page-title">Approvals</h1>
      <p className="muted">Approve or reject agents and tenants waiting for access.</p>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}
      {items.length === 0 && <p className="empty">No pending users.</p>}
      {items.map((u) => (
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
    </div>
  )
}
