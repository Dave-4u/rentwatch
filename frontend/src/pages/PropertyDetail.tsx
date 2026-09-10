import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, formatNgn, type Property } from '../api/client'
import { useAuth } from '../auth'

const TYPES = [
  'Self',
  'One bedroom',
  'Two bedroom',
  'Three bedroom',
  'Store',
  'Duplex',
]

export default function PropertyDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const nav = useNavigate()
  const [prop, setProp] = useState<Property | null>(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: '',
    address: '',
    property_type: 'One bedroom',
    description: '',
    default_rent: '',
  })
  const staff = user?.role === 'landlord' || user?.role === 'agent'

  useEffect(() => {
    api
      .property(Number(id))
      .then((p) => {
        setProp(p)
        setForm({
          name: p.name,
          address: p.address,
          property_type: p.property_type,
          description: p.description || '',
          default_rent: p.default_rent != null ? String(p.default_rent) : '',
        })
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed'))
  }, [id])

  async function onSave(e: FormEvent) {
    e.preventDefault()
    try {
      const updated = await api.updateProperty(Number(id), {
        name: form.name,
        address: form.address,
        property_type: form.property_type,
        description: form.description || undefined,
        default_rent: form.default_rent ? Number(form.default_rent) : undefined,
      })
      setProp(updated)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  async function onDelete() {
    if (!confirm('Delete this property?')) return
    try {
      await api.deleteProperty(Number(id))
      nav('/properties')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  if (error && !prop) return <div className="error">{error}</div>
  if (!prop) return <p className="muted">Loading…</p>

  return (
    <div>
      <p>
        <Link to="/properties">← Properties</Link>
      </p>
      {error && <div className="error">{error}</div>}
      {!editing ? (
        <div className="card">
          <h1 className="page-title">{prop.name}</h1>
          <p>{prop.address}</p>
          <p>
            <span className="badge pending">{prop.property_type}</span>{' '}
            {prop.default_rent != null && formatNgn(prop.default_rent)}
          </p>
          {prop.description && <p className="muted">{prop.description}</p>}
          {staff && (
            <div className="stack-actions">
              <button className="btn sm" type="button" onClick={() => setEditing(true)}>
                Edit
              </button>
              {user?.role === 'landlord' && (
                <button className="btn sm danger" type="button" onClick={onDelete}>
                  Delete
                </button>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <h2>Edit property</h2>
          <form className="form" onSubmit={onSave}>
            <label>
              Name
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </label>
            <label>
              Address
              <input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                required
              />
            </label>
            <label>
              Type
              <select
                value={form.property_type}
                onChange={(e) => setForm({ ...form, property_type: e.target.value })}
              >
                {TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Default rent
              <input
                type="number"
                value={form.default_rent}
                onChange={(e) => setForm({ ...form, default_rent: e.target.value })}
              />
            </label>
            <label>
              Description
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </label>
            <div className="stack-actions">
              <button className="btn" type="submit">
                Save
              </button>
              <button className="btn secondary" type="button" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
