import { Navigate, Outlet } from 'react-router-dom'
import { useStore } from '../stores/useStore.js'

export default function ProtectedRoute() {
  const { isAuthenticated } = useStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
