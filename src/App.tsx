import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Data from './pages/Data'
import Routes_ from './pages/Routes'
import Optimization from './pages/Optimization'
import Comparison from './pages/Comparison'
import Workload from './pages/Workload'
import Reliability from './pages/Reliability'
import Fallback from './pages/Fallback'
import Experiments from './pages/Experiments'
import Validation from './pages/Validation'
import Reports from './pages/Reports'
import Settings from './pages/Settings'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="data" element={<Data />} />
        <Route path="routes" element={<Routes_ />} />
        <Route path="optimization" element={<Optimization />} />
        <Route path="comparison" element={<Comparison />} />
        <Route path="workload" element={<Workload />} />
        <Route path="reliability" element={<Reliability />} />
        <Route path="fallback" element={<Fallback />} />
        <Route path="experiments" element={<Experiments />} />
        <Route path="validation" element={<Validation />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
