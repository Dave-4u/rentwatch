import { useEffect, useState } from 'react'
import { api, type Notification } from '../api/client'

export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([])
  const [error, setError] = useState('')

  async function load() {
    try {
      setItems(await api.notifications())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function mark(id: number) {
    await api.markRead(id)
    await load()
  }

  async function markAll() {
    await api.markAllRead()
    await load()
  }

  return (
    <div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1 className="page-title">Notifications</h1>
        <button className="btn sm secondary" type="button" onClick={markAll}>
          Mark all read
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {items.length === 0 && <p className="empty">No notifications.</p>}
      {items.map((n) => (
        <div className="card" key={n.id} style={{ opacity: n.is_read ? 0.7 : 1 }}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h3>{n.title}</h3>
            {!n.is_read && <span className="badge warn">New</span>}
          </div>
          <p>{n.message.replace(/\[overdue:[^\]]+\]/g, '').trim()}</p>
          <div className="muted">{new Date(n.created_at).toLocaleString()}</div>
          {!n.is_read && (
            <button className="btn sm" type="button" onClick={() => mark(n.id)}>
              Mark read
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
