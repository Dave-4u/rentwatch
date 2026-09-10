const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type UserRole = 'landlord' | 'agent' | 'tenant'
export type UserStatus = 'pending' | 'approved' | 'rejected' | 'suspended' | 'deleted'

export interface User {
  id: number
  email: string
  full_name: string
  phone?: string | null
  role: UserRole
  status: UserStatus
  created_at: string
}

export interface Property {
  id: number
  name: string
  address: string
  property_type: string
  description?: string | null
  default_rent?: number | null
  created_at: string
}

export interface Lease {
  id: number
  property_id: number
  tenant_id: number
  rent_amount: number
  billing_period: string
  due_day: number
  start_date: string
  status: 'active' | 'ended'
  created_at: string
  property_name?: string | null
  property_type?: string | null
  tenant_name?: string | null
  is_overdue?: boolean | null
  balance_due?: number | null
  current_period?: string | null
}

export interface Payment {
  id: number
  lease_id: number
  amount: number
  paid_on: string
  method: 'cash' | 'transfer' | 'other'
  note?: string | null
  recorded_by_id: number
  period_key: string
  created_at: string
}

export interface Notification {
  id: number
  user_id: number
  title: string
  message: string
  is_read: boolean
  created_at: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('rw_token')
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  return h
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  })
  if (res.status === 204) return undefined as T
  const text = await res.text()
  let data: unknown = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { detail: text }
  }
  if (!res.ok) {
    const detail = (data as { detail?: unknown })?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(', ')
          : res.statusText
    const err = new Error(msg || 'Request failed') as Error & { status: number }
    err.status = res.status
    throw err
  }
  return data as T
}

export const api = {
  register: (body: {
    email: string
    password: string
    full_name: string
    phone?: string
    role: 'agent' | 'tenant'
  }) => request<User>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),

  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>('/auth/me'),

  pendingUsers: () => request<User[]>('/admin/pending-users'),
  users: (role?: UserRole) =>
    request<User[]>(role ? `/admin/users?role=${role}` : '/admin/users'),
  approveUser: (id: number) => request<User>(`/admin/users/${id}/approve`, { method: 'POST' }),
  rejectUser: (id: number) => request<User>(`/admin/users/${id}/reject`, { method: 'POST' }),
  suspendUser: (id: number) => request<User>(`/admin/users/${id}/suspend`, { method: 'POST' }),
  deleteUser: (id: number) => request<User>(`/admin/users/${id}`, { method: 'DELETE' }),

  properties: () => request<Property[]>('/properties'),
  property: (id: number) => request<Property>(`/properties/${id}`),
  createProperty: (body: Partial<Property>) =>
    request<Property>('/properties', { method: 'POST', body: JSON.stringify(body) }),
  updateProperty: (id: number, body: Partial<Property>) =>
    request<Property>(`/properties/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteProperty: (id: number) => request<void>(`/properties/${id}`, { method: 'DELETE' }),

  leases: (status?: 'active' | 'ended') =>
    request<Lease[]>(status ? `/leases?status=${status}` : '/leases'),
  activeLeasesForPayment: () => request<Lease[]>('/leases/options/active'),
  createLease: (body: Record<string, unknown>) =>
    request<Lease>('/leases', { method: 'POST', body: JSON.stringify(body) }),
  updateLease: (id: number, body: Record<string, unknown>) =>
    request<Lease>(`/leases/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  tenantsForLease: () =>
    request<{ id: number; full_name: string; email: string }[]>('/leases/options/tenants'),

  payments: (leaseId?: number) =>
    request<Payment[]>(leaseId ? `/payments?lease_id=${leaseId}` : '/payments'),
  createPayment: (body: Record<string, unknown>) =>
    request<Payment>('/payments', { method: 'POST', body: JSON.stringify(body) }),

  dashboardLandlord: () => request<Record<string, unknown>>('/dashboard/landlord'),
  dashboardAgent: () => request<Record<string, unknown>>('/dashboard/agent'),
  dashboardTenant: () => request<Record<string, unknown>>('/dashboard/tenant'),

  notifications: () => request<Notification[]>('/notifications'),
  markRead: (id: number) => request<Notification>(`/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => request<{ ok: boolean }>('/notifications/read-all', { method: 'POST' }),
}

export function formatNgn(n: number | null | undefined): string {
  const v = Number(n || 0)
  return `NGN ${v.toLocaleString('en-NG', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

export function leaseLabel(l: Lease): string {
  const prop = l.property_name || `Property #${l.property_id}`
  const unit = l.property_type ? ` (${l.property_type})` : ''
  const tenant = l.tenant_name || `Tenant #${l.tenant_id}`
  return `${tenant} — ${prop}${unit} · ${formatNgn(l.rent_amount)}`
}
