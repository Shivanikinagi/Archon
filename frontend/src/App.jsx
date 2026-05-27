import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Research from './pages/Research.jsx'
import Reports from './pages/Reports.jsx'
import Graphs from './pages/Graphs.jsx'
import Settings from './pages/Settings.jsx'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/research" element={<Research />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/graphs" element={<Graphs />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App
