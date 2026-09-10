import { Settings as SettingsIcon, Lock, Info, ExternalLink } from 'lucide-react'
import { useAuthStore } from '../store/auth'

export default function Settings() {
  const { username, role, fullName } = useAuthStore()
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Settings</h1>
        <p className="text-slate-400 text-sm mt-1">System configuration and about information</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="section-title">Current User</h2>
          <div className="space-y-3">
            <div className="metric-row"><span className="metric-label">Username</span><span className="metric-value">{username}</span></div>
            <div className="metric-row"><span className="metric-label">Full Name</span><span className="metric-value">{fullName}</span></div>
            <div className="metric-row"><span className="metric-label">Role</span><span className="badge bg-primary-950 text-primary-300 border-primary-800 capitalize">{role}</span></div>
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">API Configuration</h2>
          <div className="space-y-3">
            <div className="metric-row"><span className="metric-label">Backend URL</span><span className="metric-value font-mono text-sm">http://localhost:8000</span></div>
            <div className="metric-row"><span className="metric-label">API Prefix</span><span className="metric-value font-mono text-sm">/api</span></div>
            <div className="metric-row"><span className="metric-label">Auth</span><span className="metric-value">JWT Bearer Token</span></div>
            <div className="metric-row"><span className="metric-label">Token Expiry</span><span className="metric-value">8 hours</span></div>
          </div>
          <div className="mt-4">
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
               className="btn-secondary inline-flex items-center gap-2 text-sm">
              <ExternalLink className="w-4 h-4" />Open API Docs (Swagger)
            </a>
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">System Information</h2>
          <div className="space-y-3">
            {[
              { label: 'Application', val: 'Multi-Objective School-Bus Route Planner' },
              { label: 'Version', val: '1.0.0 (Prototype)' },
              { label: 'Backend', val: 'FastAPI + SQLAlchemy + SQLite' },
              { label: 'Frontend', val: 'React 18 + Vite + TypeScript' },
              { label: 'Optimization', val: 'Clarke-Wright + 2-opt + Weighted Multi-Objective' },
              { label: 'Simulation', val: 'Monte Carlo (500 runs, lognormal)' },
              { label: 'Map', val: 'Leaflet + OpenStreetMap' },
              { label: 'Charts', val: 'Recharts' },
            ].map(item => (
              <div key={item.label} className="metric-row">
                <span className="metric-label">{item.label}</span>
                <span className="metric-value text-sm">{item.val}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">Hard Constraints (System-Enforced)</h2>
          <p className="text-slate-400 text-sm mb-4">These constraints cannot be overridden by any user.</p>
          <div className="space-y-3">
            {[
              { id: 'H1', name: 'Bus Capacity', rule: 'Route load ≤ bus seat capacity. NO exceptions.' },
              { id: 'H2', name: 'Driver Shift End', rule: 'Route completion ≤ driver shift end time.' },
              { id: 'H3', name: 'Max Driving Minutes', rule: 'Driving time ≤ max driving time per shift.' },
              { id: 'H4', name: 'Pickup Time Window', rule: 'Bus arrives within [window_start, window_end].' },
            ].map(c => (
              <div key={c.id} className="flex items-start gap-3 p-3 bg-red-950/20 border border-red-900/30 rounded-lg">
                <Lock className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="badge-hard">{c.id}</span>
                    <span className="text-sm font-medium text-red-200">{c.name}</span>
                  </div>
                  <div className="text-xs text-red-400/70 mt-1">{c.rule}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="section-title">About This System</h2>
        <div className="prose prose-sm prose-invert max-w-none text-slate-300 space-y-2 text-sm">
          <p>This application is a full-stack research prototype for Multi-Objective School-Bus Route Planning under variable student attendance. It was developed as part of a Center of Excellence (COE) project.</p>
          <p>The system implements two optimization approaches: (1) a distance-only baseline using Clarke-Wright Savings with 2-opt local search, and (2) a multi-objective optimizer balancing distance, time-window compliance, route reliability, and driver workload fairness.</p>
          <p>Reliability is quantified via Monte Carlo simulation (500 runs, lognormal travel-time distributions). The system operates offline-first with store-and-forward capability for GPS and network failures.</p>
          <p className="text-amber-400 font-medium">⚠ This is a prototype for research and demonstration purposes. All data is synthetic. Not for production use.</p>
        </div>
      </div>
    </div>
  )
}
