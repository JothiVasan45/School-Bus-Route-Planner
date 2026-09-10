import { useEffect, useState } from 'react'
import { dashboardApi, dataApi, optimizationApi } from '../api/client'
import { Bus, Users, MapPin, UserCheck, CheckCircle2, XCircle, AlertTriangle, Wifi, WifiOff, Play, Zap, RefreshCw } from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'
import toast from 'react-hot-toast'

interface DashboardData {
  summary: any
  baseline: any
  optimized: any
  system_status: any
  targets: any
}

function StatusDot({ status }: { status: string }) {
  return status === 'ONLINE'
    ? <span className="flex items-center gap-1.5 badge-online"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />ONLINE</span>
    : <span className="flex items-center gap-1.5 badge-offline"><span className="w-1.5 h-1.5 rounded-full bg-red-400" />OFFLINE</span>
}

function KPI({ label, value, icon: Icon, color, sub }: { label: string; value: string | number; icon: any; color: string; sub?: string }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-slate-400">{label}</div>
        {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [demoRunning, setDemoRunning] = useState(false)

  const load = async () => {
    try {
      const res = await dashboardApi.get()
      setData(res.data)
    } catch (e) {
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const runDemo = async () => {
    setDemoRunning(true)
    toast('🚀 Starting Demo Mode...', { icon: '🚌' })
    try {
      // Step 1: Generate data
      toast('Generating synthetic dataset (75 stops, 350 students)...')
      await dataApi.generate({ n_stops: 75, n_students: 350, n_buses: 10, n_drivers: 10, seed: 42 })
      await new Promise(r => setTimeout(r, 800))

      // Step 2: Run baseline
      toast('Running distance-only baseline optimizer...')
      await optimizationApi.run({ optimization_type: 'baseline', attendance_scenario: 'normal', run_reliability_sim: true })
      await new Promise(r => setTimeout(r, 800))

      // Step 3: Run multi-objective
      toast('Running multi-objective optimizer...')
      await optimizationApi.run({ optimization_type: 'multiobjective', attendance_scenario: 'normal', preset: 'balanced', run_reliability_sim: true })
      await new Promise(r => setTimeout(r, 800))

      await load()
      toast.success('✅ Demo loaded! Check all pages for results.')
    } catch (e) {
      toast.error('Demo failed. Is the backend running?')
    } finally {
      setDemoRunning(false)
    }
  }

  const b = data?.baseline || {}
  const m = data?.optimized || {}
  const sys = data?.system_status || {}
  const summary = data?.summary || {}

  const comparisonData = [
    { name: 'On-Time %', Baseline: b.avg_on_time_probability || 0, Optimized: m.avg_on_time_probability || 0 },
    { name: 'Reliability %', Baseline: b.avg_reliability_score || 0, Optimized: m.avg_reliability_score || 0 },
    { name: 'Dist (km/10)', Baseline: (b.total_distance_km || 0) / 10, Optimized: (m.total_distance_km || 0) / 10 },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Multi-Objective School-Bus Route Planner Overview</p>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <button onClick={runDemo} disabled={demoRunning} className="btn-primary flex items-center gap-2">
            {demoRunning ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Running Demo...</> : <><Zap className="w-4 h-4" /> Run Demo</>}
          </button>
        </div>
      </div>

      {/* System Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0">System Status</h2>
          <span className="text-xs text-slate-500">Real-time monitoring</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { key: 'gps', label: 'GPS' },
            { key: 'network', label: 'Network' },
            { key: 'attendance_feed', label: 'Attendance Feed' },
            { key: 'traffic_feed', label: 'Traffic Feed' },
          ].map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between bg-slate-800/50 rounded-lg px-3 py-2 border border-slate-700">
              <span className="text-slate-300 text-sm font-medium">{label}</span>
              <StatusDot status={sys[key] || 'ONLINE'} />
            </div>
          ))}
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPI label="Total Buses" value={summary.total_buses || 0} icon={Bus} color="bg-primary-700" />
        <KPI label="Active Drivers" value={summary.total_drivers || 0} icon={Users} color="bg-purple-700" />
        <KPI label="Bus Stops" value={summary.total_stops || 0} icon={MapPin} color="bg-sky-700" />
        <KPI label="Expected Students" value={Math.round(summary.expected_students_today || 0)} icon={UserCheck} color="bg-emerald-700" sub="Daily average" />
      </div>

      {/* Optimization comparison */}
      {(b.n_routes || m.n_routes) ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Table comparison */}
          <div className="card">
            <h2 className="section-title">Baseline vs Optimized</h2>
            <div className="space-y-3">
              {[
                { label: 'Routes', baseline: b.n_routes, optimized: m.n_routes },
                { label: 'Total Distance (km)', baseline: b.total_distance_km?.toFixed(1), optimized: m.total_distance_km?.toFixed(1), lower_better: true },
                { label: 'Avg Duration (min)', baseline: b.avg_duration_minutes?.toFixed(0), optimized: m.avg_duration_minutes?.toFixed(0), lower_better: true },
                { label: 'On-Time % ', baseline: b.avg_on_time_probability, optimized: m.avg_on_time_probability, higher_better: true, pct: true },
                { label: 'Capacity Violations', baseline: b.capacity_violations, optimized: m.capacity_violations, lower_better: true },
                { label: 'Time Window Violations', baseline: b.time_window_violations, optimized: m.time_window_violations, lower_better: true },
                { label: 'Avg Reliability %', baseline: b.avg_reliability_score, optimized: m.avg_reliability_score, higher_better: true, pct: true },
              ].map(row => (
                <div key={row.label} className="flex items-center justify-between py-2 border-b border-border/40 last:border-0">
                  <span className="text-slate-400 text-sm">{row.label}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-300 text-sm font-mono w-16 text-right">
                      {row.baseline != null ? (row.pct ? `${Number(row.baseline).toFixed(1)}%` : row.baseline) : '—'}
                    </span>
                    <span className={`text-sm font-mono w-16 text-right font-semibold ${
                      row.optimized != null && row.baseline != null
                        ? (row.lower_better
                            ? (Number(row.optimized) < Number(row.baseline) ? 'text-emerald-400' : Number(row.optimized) > Number(row.baseline) ? 'text-red-400' : 'text-slate-300')
                            : row.higher_better
                              ? (Number(row.optimized) > Number(row.baseline) ? 'text-emerald-400' : Number(row.optimized) < Number(row.baseline) ? 'text-red-400' : 'text-slate-300')
                              : 'text-slate-300')
                        : 'text-slate-300'
                    }`}>
                      {row.optimized != null ? (row.pct ? `${Number(row.optimized).toFixed(1)}%` : row.optimized) : '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-4 mt-3 text-xs text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-slate-500" />Baseline</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-primary-500" />Optimized</span>
            </div>
          </div>

          {/* Chart */}
          <div className="card">
            <h2 className="section-title">Performance Comparison</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={comparisonData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
                <Bar dataKey="Baseline" fill="#475569" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Optimized" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">🚌</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Routes Generated Yet</h3>
          <p className="text-slate-400 mb-6 text-sm">Click "Run Demo" to automatically generate a dataset, run optimizations, and populate the dashboard.</p>
          <button onClick={runDemo} disabled={demoRunning} className="btn-primary inline-flex items-center gap-2">
            <Zap className="w-4 h-4" /> Run Demo
          </button>
        </div>
      )}

      {/* Targets */}
      <div className="card">
        <h2 className="section-title">Performance Targets</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'On-Time Target', target: '≥ 95%', measured: m.avg_on_time_probability != null ? `${Number(m.avg_on_time_probability).toFixed(1)}%` : '—', pass: m.avg_on_time_probability >= 95 },
            { label: 'Capacity Violations', target: '0', measured: m.capacity_violations != null ? String(m.capacity_violations) : '—', pass: m.capacity_violations === 0 },
            { label: 'Reliability Score', target: '≥ 90%', measured: m.avg_reliability_score != null ? `${Number(m.avg_reliability_score).toFixed(1)}%` : '—', pass: m.avg_reliability_score >= 90 },
            { label: 'Distance vs Baseline', target: '≤ +15%', measured: b.total_distance_km && m.total_distance_km ? `${(((m.total_distance_km - b.total_distance_km) / b.total_distance_km) * 100).toFixed(1)}%` : '—', pass: b.total_distance_km && m.total_distance_km ? m.total_distance_km <= b.total_distance_km * 1.15 : false },
          ].map(t => (
            <div key={t.label} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">{t.label}</span>
                {t.measured !== '—' && (
                  t.pass
                    ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    : <XCircle className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div className="text-xl font-bold text-white">{t.measured}</div>
              <div className="text-xs text-slate-500 mt-1">Target: {t.target}</div>
              {t.measured !== '—' && (
                <div className={`text-xs font-semibold mt-1 ${t.pass ? 'text-emerald-400' : 'text-red-400'}`}>
                  {t.pass ? 'PASS' : 'FAIL'}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
