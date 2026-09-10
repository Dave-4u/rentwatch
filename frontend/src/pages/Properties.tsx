import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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

export default function Properties() {
  const { user } = useAuth()
  const [items, setItems] = useState<Property[]>([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '',
    address: '',
    property_type: 'One bedroom',
    description: '',
    default_rent: '',
  })
  const canCreate = user?.role === 'landlord'

  async function load() {
    try {
      setItems(await api.properties())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api.createProperty({
        name: form.name,
        address: form.address,
        property_type: form.property_type,
        description: form.description || undefined,
        default_rent: form.default_rent ? Number(form.default_rent) : undefined,
      })
      setShowForm(false)
      setForm({
        name: '',
        address: '',
        property_type: 'One bedroom',
        description: '',
        default_rent: '',
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    }
  }

  return (
    <div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1 className="page-title">Properties</h1>
        {canCreate && (
          <button className="btn sm" type="button" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : 'Add'}
          </button>
        )}
      </div>
      {error && <div className="error">{error}</div>}
      {showForm && (
        <div className="card">
          <h2>New property</h2>
          <form className="form" onSubmit={onCreate}>
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
              Default rent (NGN)
              <input
                type="number"
                min={0}
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
            <button className="btn" type="submit">
              Save property
            </button>
          </form>
        </div>
      )}
      {items.length === 0 && <p className="empty">No properties yet.</p>}
      {items.map((p) => (
        <Link key={p.id} to={`/properties/${p.id}`} className="card" style={{ display: 'block' }}>
          <h3>{p.name}</h3>
          <div className="muted">{p.address}</div>
          <div className="row" style={{ marginTop: '0.5rem' }}>
            <span className="badge pending">{p.property_type}</span>
            {p.default_rent != null && (
              <span className="muted">{formatNgn(p.default_rent)}</span>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}
