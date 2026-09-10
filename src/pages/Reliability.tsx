import { useState } from 'react'
import { simulationApi, optimizationApi } from '../api/client'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar } from 'recharts'
import { BarChart3, Play, RefreshCw, Target } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Reliability() {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [routeId, setRouteId] = useState('')
  const [simRuns, setSimRuns] = useState(500)
  const [deadline, setDeadline] = useState('08:30')

  const runSim = async () => {
    setRunning(true)
    try {
      const res = await simulationApi.run({
        route_id: routeId || undefined,
        simulation_runs: simRuns,
        required_completion: deadline,
      })
      setResults(res.data.results || [])
      toast.success(`Simulation complete: ${res.data.results?.length} routes analyzed.`)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Simulation failed. Run optimization first.')
    } finally {
      setRunning(false)
    }
  }

  // Build histogram from duration_samples
  function buildHistogram(samples: number[], bins = 20) {
    if (!samples || samples.length === 0) return []
    const min = Math.min(...samples)
    const max = Math.max(...samples)
    const binWidth = (max - min) / bins || 1
    const counts = Array(bins).fill(0)
    samples.forEach(s => {
      const idx = Math.min(Math.floor((s - min) / binWidth), bins - 1)
      counts[idx]++
    })
    return counts.map((count, i) => ({
      duration: (min + i * binWidth).toFixed(1),
      count,
      probability: (count / samples.length * 100).toFixed(1),
    }))
  }

  const selectedResult = results[0]
  const histData = selectedResult ? buildHistogram(selectedResult.duration_samples || [], 20) : []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Reliability Simulation</h1>
        <p className="text-slate-400 text-sm mt-1">Monte Carlo reliability analysis using lognormal travel-time distributions (500 runs)</p>
      </div>

      {/* Config */}
      <div className="card">
        <h2 className="section-title">Simulation Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Route ID (leave blank for all)</label>
            <input type="text" value={routeId} onChange={e => setRouteId(e.target.value)}
              className="input w-full" placeholder="e.g. R001 or leave blank" />
          </div>
          <div>
            <label className="label">Completion Deadline</label>
            <input type="time" value={deadline} onChange={e => setDeadline(e.target.value)}
              className="input w-full" />
          </div>
          <div>
            <div className="flex justify-between">
              <label className="label">Simulation Runs</label>
              <span className="text-primary-400 font-mono text-sm">{simRuns}</span>
            </div>
            <input type="range" min={100} max={2000} step={100} value={simRuns}
              onChange={e => setSimRuns(Number(e.target.value))} className="w-full accent-primary-500 mt-2" />
          </div>
        </div>
        <button onClick={runSim} disabled={running} className="btn-primary mt-4 flex items-center gap-2">
          {running ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Running {simRuns} Monte Carlo simulations...</> : <><Play className="w-4 h-4" />Run Reliability Simulation</>}
        </button>
      </div>

      {/* Results summary */}
      {results.length > 0 && (
        <div className="space-y-6 animate-slide-up">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {results.slice(0, 4).map((r, i) => (
              <div key={r.route_id} className="card-sm text-center">
                <div className="text-xs text-slate-400 mb-1">Route {i+1}: {r.route_id}</div>
                <div className={`text-3xl font-bold ${r.on_time_probability >= 0.95 ? 'text-emerald-400' : r.on_time_probability >= 0.85 ? 'text-amber-400' : 'text-red-400'}`}>
                  {(r.on_time_probability * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-slate-500">On-Time Prob.</div>
                <div className="text-xs text-slate-400 mt-1">P90: {r.p90_duration?.toFixed(0)} min</div>
              </div>
            ))}
          </div>

          {/* Detailed table */}
          <div className="card">
            <h2 className="section-title">Simulation Results</h2>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Route ID</th><th>On-Time %</th><th>Late %</th><th>P50 (min)</th><th>P90 (min)</th><th>P95 (min)</th><th>Expected (min)</th><th>Reliability Score</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map(r => (
                    <tr key={r.route_id}>
                      <td className="font-mono text-xs">{r.route_id}</td>
                      <td className={`font-bold ${r.on_time_probability >= 0.95 ? 'text-emerald-400' : r.on_time_probability >= 0.85 ? 'text-amber-400' : 'text-red-400'}`}>
                        {(r.on_time_probability * 100).toFixed(1)}%
                      </td>
                      <td className="text-red-400">{(r.late_probability * 100).toFixed(1)}%</td>
                      <td className="font-mono">{r.p50_duration?.toFixed(1)}</td>
                      <td className="font-mono">{r.p90_duration?.toFixed(1)}</td>
                      <td className="font-mono">{r.p95_duration?.toFixed(1)}</td>
                      <td className="font-mono">{r.expected_duration?.toFixed(1)}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="progress-bar w-12">
                            <div className={`progress-fill ${r.reliability_score >= 0.9 ? 'bg-emerald-500' : r.reliability_score >= 0.8 ? 'bg-amber-500' : 'bg-red-500'}`}
                              style={{ width: `${r.reliability_score * 100}%` }} />
                          </div>
                          <span className="text-xs">{(r.reliability_score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        {r.on_time_probability >= 0.95 ? <span className="badge-pass">HIGH</span>
                          : r.on_time_probability >= 0.85 ? <span className="badge-warning">MED</span>
                          : <span className="badge-fail">LOW</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Histogram */}
          {histData.length > 0 && (
            <div className="card">
              <h2 className="section-title">Duration Distribution — Route 1 ({simRuns} simulations)</h2>
              <div className="flex items-center gap-6 mb-4 text-sm">
                <span className="text-slate-400">P50: <span className="text-white font-bold">{selectedResult.p50_duration?.toFixed(0)} min</span></span>
                <span className="text-slate-400">P90: <span className="text-amber-400 font-bold">{selectedResult.p90_duration?.toFixed(0)} min</span></span>
                <span className="text-slate-400">P95: <span className="text-red-400 font-bold">{selectedResult.p95_duration?.toFixed(0)} min</span></span>
                <span className="text-slate-400">Target: <span className="text-emerald-400 font-bold">{deadline}</span></span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={histData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="duration" tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={v => `${v}m`} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                    formatter={(val: any) => [`${val} runs`, 'Frequency']} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[2,2,0,0]} opacity={0.85} />
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-slate-500 mt-2 text-center">
                Lognormal distribution of simulated route completion durations across {simRuns} Monte Carlo runs
              </p>
            </div>
          )}
        </div>
      )}

      {results.length === 0 && !running && (
        <div className="card text-center py-12">
          <BarChart3 className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">Run Reliability Simulation</h3>
          <p className="text-slate-400 text-sm">Click "Run Reliability Simulation" above to execute Monte Carlo analysis on your routes.</p>
        </div>
      )}
    </div>
  )
}
