import { useState } from 'react'
import { optimizationApi } from '../api/client'
import { Sliders, Play, Lock, AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import toast from 'react-hot-toast'

const PRESETS = {
  distance_priority: { w_distance: 0.60, w_time_window: 0.15, w_reliability: 0.15, w_workload: 0.10, label: 'Distance Priority', desc: 'Minimize total route distance above all else.' },
  balanced: { w_distance: 0.25, w_time_window: 0.30, w_reliability: 0.30, w_workload: 0.15, label: 'Balanced', desc: 'Equal balance across all objectives.' },
  reliability_priority: { w_distance: 0.15, w_time_window: 0.30, w_reliability: 0.40, w_workload: 0.15, label: 'Reliability Priority', desc: 'Prioritize on-time completion and reliability.' },
}

type WeightKey = 'w_distance' | 'w_time_window' | 'w_reliability' | 'w_workload'

export default function Optimization() {
  const [optType, setOptType] = useState<'baseline' | 'multiobjective'>('multiobjective')
  const [scenario, setScenario] = useState('normal')
  const [preset, setPreset] = useState<string | null>('balanced')
  const [weights, setWeights] = useState({ w_distance: 0.25, w_time_window: 0.30, w_reliability: 0.30, w_workload: 0.15 })
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [simRuns, setSimRuns] = useState(500)

  const applyPreset = (key: string) => {
    setPreset(key)
    const p = PRESETS[key as keyof typeof PRESETS]
    setWeights({ w_distance: p.w_distance, w_time_window: p.w_time_window, w_reliability: p.w_reliability, w_workload: p.w_workload })
  }

  const total = Object.values(weights).reduce((a, b) => a + b, 0)
  const weightsValid = Math.abs(total - 1.0) < 0.01

  const run = async () => {
    if (!weightsValid) { toast.error('Weights must sum to 100%'); return }
    setRunning(true)
    try {
      const params: any = {
        optimization_type: optType,
        attendance_scenario: scenario,
        sim_runs: simRuns,
        run_reliability_sim: true,
        ...weights,
      }
      if (preset) params.preset = preset
      const res = await optimizationApi.run(params)
      setResult(res.data)
      toast.success(`${optType === 'baseline' ? 'Baseline' : 'Multi-objective'} optimization complete! ${res.data.n_routes} routes generated.`)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Optimization failed')
    } finally {
      setRunning(false)
    }
  }

  const wLabels: { key: WeightKey; label: string; color: string; desc: string }[] = [
    { key: 'w_distance', label: 'Distance', color: 'bg-blue-500', desc: 'Minimize total route distance' },
    { key: 'w_time_window', label: 'Time Windows', color: 'bg-purple-500', desc: 'Minimize time-window violations' },
    { key: 'w_reliability', label: 'Reliability', color: 'bg-emerald-500', desc: 'Minimize late arrival probability' },
    { key: 'w_workload', label: 'Workload', color: 'bg-amber-500', desc: 'Minimize driver workload imbalance' },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Route Optimizer</h1>
        <p className="text-slate-400 text-sm mt-1">Configure and run baseline or multi-objective route optimization</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Config panel */}
        <div className="space-y-4">
          {/* Optimization type */}
          <div className="card">
            <h2 className="section-title">Optimization Type</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { val: 'baseline', label: 'Distance-Only Baseline', icon: '📏', desc: 'Minimize total distance. Hard constraints respected.' },
                { val: 'multiobjective', label: 'Multi-Objective', icon: '🎯', desc: 'Balance distance, time windows, reliability, workload.' },
              ].map(o => (
                <button key={o.val} onClick={() => setOptType(o.val as any)}
                  className={`p-4 rounded-lg border text-left transition-all ${optType === o.val ? 'border-primary-500 bg-primary-950/30' : 'border-slate-700 bg-slate-800/30 hover:border-slate-500'}`}>
                  <div className="text-2xl mb-2">{o.icon}</div>
                  <div className="text-sm font-semibold text-white">{o.label}</div>
                  <div className="text-xs text-slate-400 mt-1">{o.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Attendance scenario */}
          <div className="card">
            <h2 className="section-title">Attendance Scenario</h2>
            <div className="grid grid-cols-3 gap-2">
              {['normal', 'low', 'high', 'random', 'custom'].map(s => (
                <button key={s} onClick={() => setScenario(s)}
                  className={`py-2 px-3 rounded-lg text-sm capitalize transition-all ${scenario === s ? 'bg-primary-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
                  {s}
                </button>
              ))}
            </div>
            <div className="mt-3 text-xs text-slate-500 p-3 bg-slate-800/50 rounded-lg border border-slate-700 space-y-1">
              <p>Normal: students attend with base probability (55–98%)</p>
              <p>Low: multiply probability by 0.6</p>
              <p>High: multiply probability by 1.15 (capped at 100%)</p>
              <p>Random: each student attends independently</p>
            </div>
          </div>
        </div>

        {/* Weights panel */}
        <div className="space-y-4">
          {optType === 'multiobjective' && (
            <>
              {/* Presets */}
              <div className="card">
                <h2 className="section-title">Weight Presets</h2>
                <div className="space-y-2">
                  {Object.entries(PRESETS).map(([key, p]) => (
                    <button key={key} onClick={() => applyPreset(key)}
                      className={`w-full p-3 rounded-lg border text-left transition-all ${preset === key ? 'border-primary-500 bg-primary-950/30' : 'border-slate-700 bg-slate-800/30 hover:border-slate-500'}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-white">{p.label}</span>
                        {preset === key && <CheckCircle2 className="w-4 h-4 text-primary-400" />}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{p.desc}</div>
                      <div className="flex gap-2 mt-2">
                        {[
                          { k: 'w_distance', c: 'bg-blue-500', v: p.w_distance },
                          { k: 'w_time_window', c: 'bg-purple-500', v: p.w_time_window },
                          { k: 'w_reliability', c: 'bg-emerald-500', v: p.w_reliability },
                          { k: 'w_workload', c: 'bg-amber-500', v: p.w_workload },
                        ].map(w => (
                          <div key={w.k} className="flex-1">
                            <div className="h-1.5 bg-slate-700 rounded-full">
                              <div className={`h-full ${w.c} rounded-full`} style={{ width: `${w.v * 100}%` }} />
                            </div>
                            <div className="text-xs text-slate-500 text-center mt-0.5">{(w.v * 100).toFixed(0)}%</div>
                          </div>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Manual weights */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="section-title mb-0">Custom Weights</h2>
                  <span className={`text-sm font-bold ${weightsValid ? 'text-emerald-400' : 'text-red-400'}`}>
                    Total: {(total * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="space-y-4">
                  {wLabels.map(w => (
                    <div key={w.key}>
                      <div className="flex justify-between mb-1">
                        <div>
                          <span className="text-sm text-slate-200 font-medium">{w.label}</span>
                          <span className="text-xs text-slate-500 ml-2">{w.desc}</span>
                        </div>
                        <span className={`text-sm font-bold font-mono ${w.color.replace('bg-', 'text-')}`}>
                          {(weights[w.key] * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <input type="range" min={0} max={1} step={0.05}
                          value={weights[w.key]}
                          onChange={e => { setPreset(null); setWeights(prev => ({ ...prev, [w.key]: Number(e.target.value) })) }}
                          className="flex-1 accent-primary-500"
                        />
                        <div className="w-12 h-2 bg-slate-700 rounded-full">
                          <div className={`h-full ${w.color} rounded-full`} style={{ width: `${weights[w.key] * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {!weightsValid && (
                  <div className="mt-3 p-2 bg-red-950 border border-red-800 rounded-lg text-red-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-3 h-3" />Weights must sum to exactly 100%
                  </div>
                )}
              </div>
            </>
          )}

          {/* Simulation runs */}
          <div className="card">
            <h2 className="section-title">Monte Carlo Simulation</h2>
            <div className="flex items-center justify-between mb-2">
              <label className="label mb-0">Simulation Runs per Route</label>
              <span className="text-primary-400 font-mono text-sm font-bold">{simRuns}</span>
            </div>
            <input type="range" min={50} max={1000} step={50} value={simRuns}
              onChange={e => setSimRuns(Number(e.target.value))}
              className="w-full accent-primary-600 mb-2"
            />
            <p className="text-xs text-slate-500">Higher = more accurate reliability estimates. Recommended: 500.</p>
          </div>
        </div>
      </div>

      {/* Hard constraints notice */}
      <div className="card border-red-800/30 bg-red-950/10">
        <h2 className="section-title text-red-300">Hard Constraints (Always Enforced)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { id: 'H1', name: 'Bus Capacity', desc: 'Route load ≤ bus capacity' },
            { id: 'H2', name: 'Driver Shift End', desc: 'Route end ≤ shift end time' },
            { id: 'H3', name: 'Max Driving Time', desc: 'Driving ≤ max driving minutes' },
            { id: 'H4', name: 'Time Window', desc: 'Arrival within window [start, end]' },
          ].map(c => (
            <div key={c.id} className="p-3 rounded-lg bg-red-950/20 border border-red-900/30">
              <div className="flex items-center gap-2 mb-1">
                <span className="badge-hard">{c.id}</span>
                <Lock className="w-3 h-3 text-red-400" />
              </div>
              <div className="text-sm font-medium text-red-200">{c.name}</div>
              <div className="text-xs text-red-400/70 mt-0.5">{c.desc}</div>
              <div className="text-xs text-red-500 mt-1 font-semibold">Cannot Override</div>
            </div>
          ))}
        </div>
      </div>

      {/* Run button */}
      <button onClick={run} disabled={running || !weightsValid}
        className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-3">
        {running ? (
          <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Optimizing routes... This may take 10–30 seconds</>
        ) : (
          <><Play className="w-5 h-5" />Run {optType === 'baseline' ? 'Baseline Optimizer' : 'Multi-Objective Optimizer'}</>
        )}
      </button>

      {/* Result */}
      {result && (
        <div className="card animate-slide-up glow-blue">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <h2 className="section-title mb-0 text-emerald-300">Optimization Complete</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card-sm text-center"><div className="text-2xl font-bold text-white">{result.n_routes}</div><div className="text-xs text-slate-400">Routes</div></div>
            <div className="card-sm text-center"><div className="text-2xl font-bold text-white">{result.total_distance_km?.toFixed(1)}</div><div className="text-xs text-slate-400">Total km</div></div>
            <div className="card-sm text-center"><div className="text-2xl font-bold text-white">{result.total_capacity_violations}</div><div className="text-xs text-slate-400">Cap. Violations</div></div>
            <div className="card-sm text-center"><div className="text-2xl font-bold text-white">{result.solve_time_seconds?.toFixed(2)}s</div><div className="text-xs text-slate-400">Solve Time</div></div>
          </div>
          <div className="mt-3 p-3 bg-primary-950/30 border border-primary-800/30 rounded-lg text-sm text-primary-200">
            <Info className="w-4 h-4 inline mr-2" />
            Routes generated. View on the <strong>Routes</strong> page for the interactive map, or go to <strong>Comparison</strong> to see baseline vs optimized metrics.
          </div>
        </div>
      )}
    </div>
  )
}
