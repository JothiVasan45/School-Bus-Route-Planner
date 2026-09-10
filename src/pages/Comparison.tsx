import { useEffect, useState } from 'react'
import { comparisonApi } from '../api/client'
import { CheckCircle2, XCircle, ArrowUp, ArrowDown, RefreshCw, GitCompare } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'
import toast from 'react-hot-toast'

export default function Comparison() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await comparisonApi.get()
      setData(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Run both baseline and optimized routes first.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400">Loading comparison...</p>
      </div>
    </div>
  )

  if (error || !data) return (
    <div className="card text-center py-16">
      <GitCompare className="w-10 h-10 text-slate-500 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-white mb-2">Comparison Not Available</h3>
      <p className="text-slate-400 mb-4 text-sm">{error}</p>
      <button onClick={load} className="btn-primary inline-flex items-center gap-2"><RefreshCw className="w-4 h-4" />Retry</button>
    </div>
  )

  const b = data.baseline
  const m = data.optimized
  const impr = data.improvements || {}

  const chartData = [
    { metric: 'Distance (km)', Baseline: b.total_distance_km, Optimized: m.total_distance_km },
    { metric: 'Duration (min)', Baseline: b.total_duration_minutes, Optimized: m.total_duration_minutes },
    { metric: 'Cap Violations', Baseline: b.capacity_violations, Optimized: m.capacity_violations },
    { metric: 'TW Violations', Baseline: b.time_window_violations, Optimized: m.time_window_violations },
    { metric: 'Workload Var', Baseline: b.workload_variance, Optimized: m.workload_variance },
  ]

  const radarData = [
    { subject: 'On-Time', Baseline: b.on_time_pct, Optimized: m.on_time_pct },
    { subject: 'Reliability', Baseline: b.avg_reliability, Optimized: m.avg_reliability },
    { subject: 'Cap OK', Baseline: b.capacity_violations === 0 ? 100 : 50, Optimized: m.capacity_violations === 0 ? 100 : 50 },
    { subject: 'TW OK', Baseline: b.time_window_violations === 0 ? 100 : 60, Optimized: m.time_window_violations === 0 ? 100 : 70 },
    { subject: 'Workload Fair', Baseline: Math.max(0, 100 - b.workload_variance / 10), Optimized: Math.max(0, 100 - m.workload_variance / 10) },
  ]

  function ImprovementBadge({ imp }: { imp: any }) {
    if (!imp) return <span className="text-slate-500 text-xs">—</span>
    return (
      <span className={`flex items-center gap-1 text-xs font-semibold ${imp.improved ? 'text-emerald-400' : 'text-red-400'}`}>
        {imp.improved ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
        {imp.pct > 0 ? '+' : ''}{imp.pct?.toFixed(1)}%
      </span>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Baseline vs Optimized</h1>
          <p className="text-slate-400 text-sm mt-1">Side-by-side performance comparison across all metrics</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw className="w-4 h-4" />Refresh</button>
      </div>

      {/* Metric comparison table */}
      <div className="card">
        <h2 className="section-title">Metric Comparison</h2>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Metric</th>
                <th className="text-slate-400">Baseline</th>
                <th className="text-primary-300">Optimized</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Routes', b_val: b.n_routes, m_val: m.n_routes },
                { label: 'Total Distance (km)', b_val: b.total_distance_km?.toFixed(2), m_val: m.total_distance_km?.toFixed(2), imp: impr.total_distance_km },
                { label: 'Avg Duration (min)', b_val: b.avg_duration_minutes?.toFixed(1), m_val: m.avg_duration_minutes?.toFixed(1), imp: impr.total_distance_km },
                { label: 'On-Time % (avg)', b_val: `${b.on_time_pct?.toFixed(1)}%`, m_val: `${m.on_time_pct?.toFixed(1)}%`, imp: impr.on_time_pct },
                { label: 'Late Probability %', b_val: `${b.late_probability_pct?.toFixed(1)}%`, m_val: `${m.late_probability_pct?.toFixed(1)}%` },
                { label: 'Capacity Violations', b_val: b.capacity_violations, m_val: m.capacity_violations, imp: impr.capacity_violations },
                { label: 'Time Window Violations', b_val: b.time_window_violations, m_val: m.time_window_violations, imp: impr.time_window_violations },
                { label: 'Shift Violations', b_val: b.shift_violations, m_val: m.shift_violations },
                { label: 'Workload Variance', b_val: b.workload_variance?.toFixed(2), m_val: m.workload_variance?.toFixed(2), imp: impr.workload_variance },
                { label: 'Max Workload Score', b_val: b.max_workload?.toFixed(1), m_val: m.max_workload?.toFixed(1) },
                { label: 'Avg Reliability %', b_val: `${b.avg_reliability?.toFixed(1)}%`, m_val: `${m.avg_reliability?.toFixed(1)}%`, imp: impr.avg_reliability },
              ].map(row => (
                <tr key={row.label}>
                  <td className="font-medium">{row.label}</td>
                  <td className="text-slate-400 font-mono">{row.b_val}</td>
                  <td className="font-mono text-primary-200">{row.m_val}</td>
                  <td><ImprovementBadge imp={row.imp} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="section-title">Key Metrics Bar Comparison</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-20} textAnchor="end" />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px', paddingTop: '8px' }} />
              <Bar dataKey="Baseline" fill="#475569" radius={[4,4,0,0]} />
              <Bar dataKey="Optimized" fill="#3b82f6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="section-title">Radar: Performance Profile</h2>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Radar name="Baseline" dataKey="Baseline" stroke="#475569" fill="#475569" fillOpacity={0.3} />
              <Radar name="Optimized" dataKey="Optimized" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Target results */}
      <div className="card">
        <h2 className="section-title">Target Achievement</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.target_results?.map((t: any) => (
            <div key={t.metric} className={`p-4 rounded-lg border ${t.status === 'PASS' ? 'border-emerald-800/30 bg-emerald-950/20' : 'border-red-800/30 bg-red-950/20'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white text-sm">{t.metric}</span>
                {t.status === 'PASS'
                  ? <span className="badge-pass flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />PASS</span>
                  : <span className="badge-fail flex items-center gap-1"><XCircle className="w-3 h-3" />FAIL</span>}
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div><span className="text-slate-500">Baseline</span><div className="font-mono text-slate-300 font-semibold">{t.baseline}</div></div>
                <div><span className="text-slate-500">Target</span><div className="font-mono text-primary-300 font-semibold">{t.target}</div></div>
                <div><span className="text-slate-500">Achieved</span><div className={`font-mono font-semibold ${t.status === 'PASS' ? 'text-emerald-300' : 'text-red-300'}`}>{t.measured}</div></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
