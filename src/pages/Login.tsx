import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { Bus, Lock, User, Eye, EyeOff, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(username, password)
      toast.success('Welcome back!')
      navigate('/dashboard')
    } catch {
      setError('Invalid username or password. Try admin/admin123 or driver/driver123')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (u: string, p: string) => {
    setUsername(u)
    setPassword(p)
    setLoading(true)
    setError('')
    try {
      await login(u, p)
      navigate('/dashboard')
    } catch {
      setError('Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4"
         style={{ background: 'radial-gradient(ellipse at 60% 40%, rgba(30,64,175,0.15) 0%, #0f172a 60%)' }}>
      <div className="w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4 shadow-lg shadow-primary-600/30">
            <Bus className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold gradient-text">BusRoute Pro</h1>
          <p className="text-slate-400 mt-2 text-sm">Multi-Objective School-Bus Route Planner</p>
        </div>

        {/* Card */}
        <div className="card glow-blue">
          <h2 className="text-xl font-semibold text-white mb-6">Sign In</h2>

          {error && (
            <div className="flex items-start gap-3 bg-red-950 border border-red-800 rounded-lg p-3 mb-4 text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="input w-full pl-10"
                  placeholder="admin or driver"
                  required
                />
              </div>
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input w-full pl-10 pr-10"
                  placeholder="admin123 or driver123"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  onClick={() => setShowPw(!showPw)}
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Quick login */}
          <div className="mt-6 pt-6 border-t border-border">
            <p className="text-slate-500 text-xs text-center mb-3">Demo Credentials</p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => quickLogin('admin', 'admin123')}
                className="btn-secondary text-sm"
                disabled={loading}
              >
                🎯 Login as Admin
              </button>
              <button
                onClick={() => quickLogin('driver', 'driver123')}
                className="btn-secondary text-sm"
                disabled={loading}
              >
                🚌 Login as Driver
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-slate-600 text-xs mt-6">
          Multi-Objective School-Bus Route Planner — Prototype v1.0
        </p>
      </div>
    </div>
  )
}
