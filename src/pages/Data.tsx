import { useState, useEffect } from 'react'
import { dataApi } from '../api/client'
import { Database, RefreshCw, CheckCircle2, AlertTriangle, Download } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Data() {
  const [stats, setStats] = useState<any>(null)
  const [preview, setPreview] = useState<any>(null)
  const [generating, setGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState<'stops' | 'buses' | 'drivers' | 'students'>('stops')
  const [config, setConfig] = useState({ n_stops: 75, n_students: 350, n_buses: 10, n_drivers: 10, seed: 42 })

  const loadStats = async () => {
    try {
      const [statsRes, previewRes] = await Promise.all([dataApi.stats(), dataApi.preview()])
      setStats(statsRes.data)
      setPreview(previewRes.data)
    } catch {}
  }

  useEffect(() => { loadStats() }, [])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await dataApi.generate(config)
      toast.success('Dataset generated successfully!')
      await loadStats()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  const tabs = ['stops', 'buses', 'drivers', 'students'] as const

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Dataset Management</h1>
          <p className="text-slate-400 text-sm mt-1">Generate, upload, validate and preview the school-bus dataset</p>
        </div>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { label: 'Stops', val: stats.n_stops },
            { label: 'Students', val: stats.n_students },
            { label: 'Buses', val: stats.n_buses },
            { label: 'Drivers', val: stats.n_drivers },
            { label: 'Travel Time Pairs', val: stats.n_travel_time_pairs },
            { label: 'Expected Daily', val: Math.round(stats.total_expected_daily_students) },
          ].map(s => (
            <div key={s.label} className="card-sm text-center">
              <div className="text-2xl font-bold text-white">{s.val}</div>
              <div className="text-xs text-slate-400">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generate panel */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-primary-400" />
            <h2 className="section-title mb-0">Generate Synthetic Dataset</h2>
          </div>
          <p className="text-slate-400 text-sm mb-4">Generate a realistic Chennai metropolitan area school-bus network with lognormal travel-time distributions.</p>

          <div className="space-y-3">
            {[
              { key: 'n_stops', label: 'Bus Stops', min: 10, max: 100 },
              { key: 'n_students', label: 'Students', min: 50, max: 500 },
              { key: 'n_buses', label: 'Buses', min: 3, max: 20 },
              { key: 'n_drivers', label: 'Drivers', min: 3, max: 20 },
              { key: 'seed', label: 'Random Seed', min: 1, max: 9999 },
            ].map(f => (
              <div key={f.key}>
                <div className="flex justify-between mb-1">
                  <label className="label mb-0">{f.label}</label>
                  <span className="text-sm text-primary-400 font-mono">{config[f.key as keyof typeof config]}</span>
                </div>
                <input
                  type="range"
                  min={f.min}
                  max={f.max}
                  value={config[f.key as keyof typeof config]}
                  onChange={e => setConfig(c => ({ ...c, [f.key]: Number(e.target.value) }))}
                  className="w-full accent-primary-600"
                />
              </div>
            ))}
          </div>

          <button onClick={handleGenerate} disabled={generating} className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
            {generating ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Generating...</> : <><RefreshCw className="w-4 h-4" />Generate Dataset</>}
          </button>

          <div className="mt-4 p-3 bg-slate-800/50 rounded-lg text-xs text-slate-400 space-y-1 border border-slate-700">
            <p>✓ Chennai-area stop names (fictional, plausible)</p>
            <p>✓ 5 geographic zones (A–E)</p>
            <p>✓ Pickup/drop-off time windows per zone</p>
            <p>✓ Lognormal travel-time distributions</p>
            <p>✓ Bus capacities: 20, 30, 40, 50 seats</p>
            <p>✓ Driver shift limits (3–3.5 hours)</p>
            <p>✓ Attendance probabilities (55–98%)</p>
          </div>
        </div>

        {/* Preview panel */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0">Data Preview</h2>
            {stats?.data_ready && <span className="badge-pass flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />Data Ready</span>}
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b border-border">
            {tabs.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${
                  activeTab === tab
                    ? 'text-primary-400 border-primary-500'
                    : 'text-slate-500 border-transparent hover:text-slate-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {!preview && (
            <div className="text-center py-12 text-slate-500">
              <Database className="w-8 h-8 mx-auto mb-3 opacity-30" />
              <p>No data yet. Click "Generate Dataset" to create a synthetic dataset.</p>
            </div>
          )}

          {preview && activeTab === 'stops' && (
            <div className="table-wrapper overflow-y-auto max-h-96">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th><th>Name</th><th>Zone</th><th>Students</th><th>Attendance</th><th>Pickup Window</th><th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.stops?.map((s: any) => (
                    <tr key={s.stop_id}>
                      <td className="font-mono text-xs text-slate-400">{s.stop_id}</td>
                      <td className="font-medium text-slate-200">{s.stop_name}</td>
                      <td><span className="badge bg-primary-950 text-primary-300 border border-primary-800">{s.zone}</span></td>
                      <td>{s.student_count}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="progress-bar w-16">
                            <div className="progress-fill bg-emerald-500" style={{ width: `${s.attendance_probability * 100}%` }} />
                          </div>
                          <span className="text-xs">{(s.attendance_probability * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="text-xs font-mono">{s.pickup_window_start}–{s.pickup_window_end}</td>
                      <td>
                        <span className={`badge ${s.priority === 1 ? 'bg-red-950 text-red-300 border-red-800' : s.priority === 2 ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                          {s.priority === 1 ? 'HIGH' : s.priority === 2 ? 'MED' : 'LOW'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {preview && activeTab === 'buses' && (
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Bus ID</th><th>Registration</th><th>Capacity</th><th>Available</th><th>Fuel</th></tr></thead>
                <tbody>
                  {preview.buses?.map((b: any) => (
                    <tr key={b.bus_id}>
                      <td className="font-mono text-xs">{b.bus_id}</td>
                      <td className="font-medium">{b.registration}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="progress-bar w-12">
                            <div className="progress-fill bg-primary-500" style={{ width: `${(b.capacity / 50) * 100}%` }} />
                          </div>
                          <span className="font-bold text-white">{b.capacity}</span>
                        </div>
                      </td>
                      <td className="text-xs font-mono">{b.available_start_time}–{b.available_end_time}</td>
                      <td><span className="badge bg-slate-800 text-slate-300 border-slate-600">{b.fuel_type}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {preview && activeTab === 'drivers' && (
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Driver ID</th><th>Name</th><th>Shift</th><th>Max Shift (min)</th><th>Max Drive (min)</th><th>Available</th></tr></thead>
                <tbody>
                  {preview.drivers?.map((d: any) => (
                    <tr key={d.driver_id}>
                      <td className="font-mono text-xs">{d.driver_id}</td>
                      <td className="font-medium">{d.driver_name}</td>
                      <td className="font-mono text-xs">{d.shift_start}–{d.shift_end}</td>
                      <td>{d.max_shift_minutes}</td>
                      <td>{d.max_driving_minutes}</td>
                      <td>{d.availability ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-amber-400" />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {preview && activeTab === 'students' && (
            <div className="table-wrapper overflow-y-auto max-h-96">
              <table className="table">
                <thead><tr><th>Student ID</th><th>Name</th><th>Stop</th><th>Grade</th><th>Attendance Prob.</th></tr></thead>
                <tbody>
                  {preview.students?.map((s: any) => (
                    <tr key={s.student_id}>
                      <td className="font-mono text-xs">{s.student_id}</td>
                      <td className="font-medium">{s.name}</td>
                      <td className="font-mono text-xs text-primary-400">{s.stop_id}</td>
                      <td>Grade {s.grade}</td>
                      <td>{(s.attendance_probability * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
