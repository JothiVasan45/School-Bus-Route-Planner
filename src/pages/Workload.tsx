import { useEffect, useState } from 'react'
import { workloadApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Users, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Workload() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [type, setType] = useState<'multiobjective' | 'baseline'>('multiobjective')

  const load = async () => {
    setLoading(true)
    try {
      const res = await workloadApi.get(type)
      setData(res.data)
    } catch (e: any) {
      toast.error('Could not load workload data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [type])

  const drivers = data?.drivers || []
  const fairness = data?.fairness || {}

  const chartData = drivers.map((d: any) => ({
    name: d.driver_name || d.driver_id,
    'Workload Score': Number(d.workload_score?.toFixed(1)),
    'Drive Min': d.driving_minutes,
    'Stops': d.stop_count,
  }))

  const imbalance = fairness.workload_imbalance || 0

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Driver Workload</h1>
          <p className="text-slate-400 text-sm mt-1">Workload distribution and fairness analysis</p>
        </div>
        <div className="flex gap-3">
          <select className="select text-sm" value={type} onChange={e => setType(e.target.value as any)}>
            <option value="multiobjective">Optimized Routes</option>
            <option value="baseline">Baseline Routes</option>
          </select>
          <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw className="w-4 h-4" />Refresh</button>
        </div>
      </div>

      {/* Fairness summary */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Workload Variance', val: fairness.workload_variance?.toFixed(2), status: fairness.workload_variance < 200 ? 'good' : 'warning' },
            { label: 'Imbalance Index', val: `${imbalance?.toFixed(1)}%`, status: imbalance < 20 ? 'good' : imbalance < 35 ? 'warning' : 'critical' },
            { label: 'Max Workload', val: fairness.max_workload?.toFixed(1), status: 'neutral' },
            { label: 'Min Workload', val: fairness.min_workload?.toFixed(1), status: 'neutral' },
          ].map(item => (
            <div key={item.label} className="card-sm text-center">
              <div className={`text-2xl font-bold ${item.status === 'good' ? 'text-emerald-400' : item.status === 'warning' ? 'text-amber-400' : item.status === 'critical' ? 'text-red-400' : 'text-white'}`}>{item.val || '—'}</div>
              <div className="text-xs text-slate-400 mt-1">{item.label}</div>
              {item.status === 'good' && <CheckCircle2 className="w-3 h-3 text-emerald-400 mx-auto mt-1" />}
              {(item.status === 'warning' || item.status === 'critical') && <AlertTriangle className="w-3 h-3 text-amber-400 mx-auto mt-1" />}
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !data || drivers.length === 0 ? (
        <div className="card text-center py-12">
          <Users className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400">No workload data. Run optimization first.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div className="card">
            <h2 className="section-title">Workload Score by Driver</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
                <ReferenceLine y={fairness.avg_workload} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'Avg', fill: '#f59e0b', fontSize: 10 }} />
                <Bar dataKey="Workload Score" fill="#3b82f6" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Minutes chart */}
          <div className="card">
            <h2 className="section-title">Driving Time by Driver</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
                <ReferenceLine y={180} stroke="#ef4444" strokeDasharray="4 2" label={{ value: 'Limit', fill: '#ef4444', fontSize: 10 }} />
                <Bar dataKey="Drive Min" fill="#8b5cf6" radius={[4,4,0,0]} />
                <Bar dataKey="Stops" fill="#10b981" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Driver table */}
          <div className="card lg:col-span-2">
            <h2 className="section-title">Driver Workload Details</h2>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Driver</th><th>Route</th><th>Duration (min)</th><th>Drive (min)</th><th>Stops</th><th>Students</th><th>Workload Score</th><th>Utilization</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {drivers.map((d: any) => {
                    const util = d.driving_minutes && d.max_driving_minutes ? (d.driving_minutes / d.max_driving_minutes) * 100 : 0
                    return (
                      <tr key={d.driver_id}>
                        <td className="font-medium">{d.driver_name || d.driver_id}</td>
                        <td className="font-mono text-xs text-slate-400">{d.route_id}</td>
                        <td>{d.total_duration_minutes?.toFixed(0)}</td>
                        <td>{d.driving_minutes?.toFixed(0)}</td>
                        <td>{d.stop_count}</td>
                        <td>{d.total_students}</td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="progress-bar w-16">
                              <div className="progress-fill bg-primary-500" style={{ width: `${Math.min(d.workload_score, 100)}%` }} />
                            </div>
                            <span className="font-mono text-xs font-bold">{d.workload_score?.toFixed(1)}</span>
                          </div>
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="progress-bar w-16">
                              <div className={`progress-fill ${util > 90 ? 'bg-red-500' : util > 70 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(util, 100)}%` }} />
                            </div>
                            <span className="text-xs">{util.toFixed(0)}%</span>
                          </div>
                        </td>
                        <td>
                          {d.shift_violation ? <span className="badge-fail">SHIFT EXCEEDED</span>
                            : d.workload_score > 80 ? <span className="badge-warning">HIGH LOAD</span>
                            : <span className="badge-pass">NORMAL</span>}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
