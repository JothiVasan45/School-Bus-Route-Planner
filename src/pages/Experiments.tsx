import { useState } from 'react'
import { experimentsApi } from '../api/client'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line, ReferenceLine } from 'recharts'
import { FlaskConical, Play, RefreshCw, BarChart3 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Experiments() {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [config, setConfig] = useState({ n_scenarios: 20, sim_runs_per_scenario: 100, seed: 42 })

  const run = async () => {
    setRunning(true)
    try {
      const res = await experimentsApi.run(config)
      setResults(res.data)
      toast.success(`Experiments complete! ${res.data.n_scenarios * 2} optimization runs across ${res.data.n_scenarios} scenarios.`)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Experiments failed. Generate dataset first.')
    } finally {
      setRunning(false)
    }
  }

  const scenarios = results?.results || []
  const baselineResults = scenarios.filter((r: any) => r.optimization_type === 'baseline')
  const moResults = scenarios.filter((r: any) => r.optimization_type === 'multiobjective')

  const lineData = baselineResults.map((br: any, i: number) => {
    const mo = moResults[i]
    return {
      scenario: i + 1,
      'Baseline OTP': br.on_time_probability,
      'Optimized OTP': mo?.on_time_probability,
      'Baseline Dist': br.total_distance_km,
      'Optimized Dist': mo?.total_distance_km,
    }
  })

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Experiment Suite</h1>
        <p className="text-slate-400 text-sm mt-1">Multi-scenario comparison: baseline vs multi-objective across attendance & traffic conditions</p>
      </div>

      {/* Config */}
      <div className="card">
        <h2 className="section-title">Experiment Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex justify-between mb-1">
              <label className="label mb-0">Number of Scenarios</label>
              <span className="text-primary-400 font-mono text-sm">{config.n_scenarios}</span>
            </div>
            <input type="range" min={5} max={50} step={5} value={config.n_scenarios}
              onChange={e => setConfig(c => ({ ...c, n_scenarios: Number(e.target.value) }))} className="w-full accent-primary-500" />
            <p className="text-xs text-slate-500 mt-1">Scenarios span: normal/low/high/random attendance × normal/heavy/light traffic</p>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <label className="label mb-0">MC Runs per Scenario</label>
              <span className="text-primary-400 font-mono text-sm">{config.sim_runs_per_scenario}</span>
            </div>
            <input type="range" min={50} max={500} step={50} value={config.sim_runs_per_scenario}
              onChange={e => setConfig(c => ({ ...c, sim_runs_per_scenario: Number(e.target.value) }))} className="w-full accent-primary-500" />
          </div>
          <div>
            <label className="label">Random Seed</label>
            <input type="number" value={config.seed} onChange={e => setConfig(c => ({ ...c, seed: Number(e.target.value) }))}
              className="input w-full" />
          </div>
        </div>
        <div className="mt-4 p-3 bg-slate-800/50 border border-slate-700 rounded-lg text-xs text-slate-400">
          This will run <strong className="text-white">{config.n_scenarios * 2} optimization runs</strong> ({config.n_scenarios} scenarios × 2 methods) with {config.sim_runs_per_scenario} MC simulations each. Estimated time: {Math.round(config.n_scenarios * 0.3 * 2)} – {Math.round(config.n_scenarios * 1.5 * 2)} seconds.
        </div>
        <button onClick={run} disabled={running} className="btn-primary mt-4 flex items-center gap-2">
          {running ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Running {config.n_scenarios * 2} experiments...</> : <><Play className="w-4 h-4" />Run Experiment Suite</>}
        </button>
      </div>

      {results && (
        <div className="space-y-6 animate-slide-up">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card-sm text-center">
              <div className="text-3xl font-bold text-white">{results.n_scenarios}</div>
              <div className="text-xs text-slate-400">Scenarios</div>
            </div>
            <div className="card-sm text-center">
              <div className="text-3xl font-bold text-white">{results.total_runs}</div>
              <div className="text-xs text-slate-400">Total Optimization Runs</div>
            </div>
            <div className="card-sm text-center">
              <div className="text-3xl font-bold text-emerald-400">{results.optimized_avg?.on_time_probability?.toFixed(1)}%</div>
              <div className="text-xs text-slate-400">Avg Optimized OTP</div>
            </div>
            <div className="card-sm text-center">
              <div className="text-3xl font-bold text-slate-400">{results.baseline_avg?.on_time_probability?.toFixed(1)}%</div>
              <div className="text-xs text-slate-400">Avg Baseline OTP</div>
            </div>
          </div>

          {/* Summary comparison */}
          <div className="card">
            <h2 className="section-title">Aggregate Results: Baseline vs Optimized</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { label: 'Avg Total Distance (km)', b: results.baseline_avg?.total_distance_km, o: results.optimized_avg?.total_distance_km, lower: true },
                { label: 'Avg On-Time %', b: results.baseline_avg?.on_time_probability, o: results.optimized_avg?.on_time_probability, higher: true },
                { label: 'Avg Cap Violations', b: results.baseline_avg?.capacity_violations, o: results.optimized_avg?.capacity_violations, lower: true },
                { label: 'Avg Workload Variance', b: results.baseline_avg?.workload_variance, o: results.optimized_avg?.workload_variance, lower: true },
              ].map(m => {
                const improved = m.lower ? m.o < m.b : m.o > m.b
                return (
                  <div key={m.label}>
                    <div className="text-xs text-slate-400 mb-2">{m.label}</div>
                    <div className="space-y-1">
                      <div className="flex justify-between"><span className="text-xs text-slate-500">Baseline</span><span className="font-mono text-sm text-slate-300">{m.b?.toFixed(2)}</span></div>
                      <div className="flex justify-between"><span className="text-xs text-slate-500">Optimized</span><span className={`font-mono text-sm font-bold ${improved ? 'text-emerald-400' : 'text-red-400'}`}>{m.o?.toFixed(2)}</span></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Line chart: OTP across scenarios */}
          {lineData.length > 0 && (
            <div className="card">
              <h2 className="section-title">On-Time Probability Across Scenarios</h2>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={lineData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="scenario" tick={{ fill: '#94a3b8', fontSize: 11 }} label={{ value: 'Scenario', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                  <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
                  <ReferenceLine y={95} stroke="#10b981" strokeDasharray="4 2" label={{ value: 'Target 95%', fill: '#10b981', fontSize: 10 }} />
                  <Line type="monotone" dataKey="Baseline OTP" stroke="#475569" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="Optimized OTP" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Results table */}
          <div className="card">
            <h2 className="section-title">Detailed Results ({scenarios.length} runs)</h2>
            <div className="table-wrapper overflow-y-auto" style={{ maxHeight: '400px' }}>
              <table className="table text-xs">
                <thead>
                  <tr>
                    <th>#</th><th>Attendance</th><th>Traffic</th><th>Type</th><th>Distance km</th><th>OTP %</th><th>Cap Viol</th><th>Workload Var</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarios.map((r: any, i: number) => (
                    <tr key={i}>
                      <td>{r.scenario_index + 1}</td>
                      <td className="capitalize">{r.scenario}</td>
                      <td className="capitalize">{r.traffic}</td>
                      <td>
                        <span className={`badge ${r.optimization_type === 'baseline' ? 'bg-slate-800 text-slate-400 border-slate-700' : 'bg-primary-950 text-primary-300 border-primary-800'}`}>
                          {r.optimization_type === 'baseline' ? 'BASE' : 'OPT'}
                        </span>
                      </td>
                      <td className="font-mono">{r.total_distance_km}</td>
                      <td className={`font-mono font-bold ${r.on_time_probability >= 95 ? 'text-emerald-400' : r.on_time_probability >= 85 ? 'text-amber-400' : 'text-red-400'}`}>
                        {r.on_time_probability}%
                      </td>
                      <td className={r.capacity_violations > 0 ? 'text-red-400 font-bold' : 'text-emerald-400'}>{r.capacity_violations}</td>
                      <td className="font-mono">{r.workload_variance}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!results && !running && (
        <div className="card text-center py-12">
          <FlaskConical className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">Run the Experiment Suite</h3>
          <p className="text-slate-400 text-sm">Compare baseline vs multi-objective across multiple attendance and traffic scenarios.</p>
        </div>
      )}
    </div>
  )
}
