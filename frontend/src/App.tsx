import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import Approvals from './pages/Approvals'
import Home from './pages/Home'
import Leases from './pages/Leases'
import Login from './pages/Login'
import NotificationsPage from './pages/Notifications'
import PaymentNew from './pages/PaymentNew'
import Pending from './pages/Pending'
import Properties from './pages/Properties'
import PropertyDetail from './pages/PropertyDetail'
import Register from './pages/Register'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/pending"
        element={
          <RequireAuth>
            <Pending />
          </RequireAuth>
        }
      />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Home />} />
        <Route path="/properties" element={<Properties />} />
        <Route path="/properties/:id" element={<PropertyDetail />} />
        <Route path="/leases" element={<Leases />} />
        <Route path="/payments/new" element={<PaymentNew />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/notifications" element={<NotificationsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
