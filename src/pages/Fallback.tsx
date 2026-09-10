import { useState, useEffect } from 'react'
import { fallbackApi } from '../api/client'
import { WifiOff, Wifi, AlertTriangle, CheckCircle2, RefreshCw, Upload, Send } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Fallback() {
  const [status, setStatus] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [queue, setQueue] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [manualForm, setManualForm] = useState({ route_id: '', stop_id: '', update_type: 'arrived', driver_id: 'DRV01', actual_time: '', student_count: 0 })
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [sRes, eRes, qRes] = await Promise.all([
        fallbackApi.status(),
        fallbackApi.events(),
        fallbackApi.queue(),
      ])
      setStatus(sRes.data)
      setEvents(eRes.data)
      setQueue(qRes.data.items || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const toggle = async (eventType: string) => {
    const currentStatus = status?.status
    const statusKey: Record<string, string> = {
      gps_failure: 'gps', network_failure: 'network',
      attendance_feed_failure: 'attendance_feed', traffic_feed_failure: 'traffic_feed',
    }
    const isActive = currentStatus?.[statusKey[eventType]] === 'OFFLINE'
    setToggling(eventType)
    try {
      await fallbackApi.toggle({ event_type: eventType, active: !isActive })
      toast[!isActive ? 'error' : 'success'](!isActive ? `${eventType} activated — entering fallback mode!` : `${eventType} resolved!`)
      await load()
    } catch (e: any) {
      toast.error('Toggle failed')
    } finally {
      setToggling(null)
    }
  }

  const sync = async () => {
    setSyncing(true)
    try {
      const res = await fallbackApi.sync()
      toast.success(res.data.message)
      await load()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const submitManual = async () => {
    setSubmitting(true)
    try {
      const res = await fallbackApi.manualUpdate(manualForm)
      toast[res.data.queued ? 'error' : 'success'](res.data.message)
      await load()
    } catch (e: any) {
      toast.error('Manual update failed')
    } finally {
      setSubmitting(false)
    }
  }

  const sysStatus = status?.status || {}
  const failures = [
    { type: 'gps_failure', label: 'GPS', key: 'gps', icon: '📡', desc: 'Simulates GPS tracker going offline. Activates manual stop-update mode.' },
    { type: 'network_failure', label: 'Network', key: 'network', icon: '🌐', desc: 'Simulates internet failure. Activates store-and-forward offline mode.' },
    { type: 'attendance_feed_failure', label: 'Attendance Feed', key: 'attendance_feed', icon: '📋', desc: 'Simulates attendance data being unavailable. Uses historical probabilities.' },
    { type: 'traffic_feed_failure', label: 'Traffic Feed', key: 'traffic_feed', icon: '🚦', desc: 'Simulates real-time traffic data being unavailable. Uses historical travel times.' },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Fallback Mode</h1>
          <p className="text-slate-400 text-sm mt-1">Offline resilience testing, store-and-forward sync, and manual stop updates</p>
        </div>
        <button onClick={load} disabled={loading} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />Refresh
        </button>
      </div>

      {/* System Status Panel */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0">System Status</h2>
          <div className="flex items-center gap-2">
            {status?.offline_mode ? (
              <span className="badge-offline flex items-center gap-1"><WifiOff className="w-3 h-3" />OFFLINE MODE</span>
            ) : (
              <span className="badge-online flex items-center gap-1"><Wifi className="w-3 h-3" />ALL SYSTEMS ONLINE</span>
            )}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {failures.map(f => {
            const isOffline = sysStatus[f.key] === 'OFFLINE'
            const isToggling = toggling === f.type
            return (
              <div key={f.type} className={`p-4 rounded-xl border transition-all ${isOffline ? 'border-red-700/50 bg-red-950/20' : 'border-slate-700 bg-slate-800/30'}`}>
                <div className="text-2xl mb-2">{f.icon}</div>
                <div className="text-sm font-semibold text-white mb-1">{f.label}</div>
                <div className="text-xs text-slate-500 mb-3 min-h-[32px]">{f.desc}</div>
                <div className="flex items-center justify-between">
                  {isOffline ? <span className="badge-offline">OFFLINE</span> : <span className="badge-online">ONLINE</span>}
                  <button onClick={() => toggle(f.type)} disabled={!!toggling}
                    className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${isOffline ? 'bg-emerald-700 hover:bg-emerald-600 text-white' : 'bg-red-700 hover:bg-red-600 text-white'}`}>
                    {isToggling ? '...' : isOffline ? 'Resolve' : 'Simulate Failure'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Store and Forward Sync */}
        <div className="card">
          <h2 className="section-title">Store-and-Forward Queue</h2>
          <div className="flex items-center gap-4 mb-4">
            <div className="text-3xl font-bold text-white">{status?.pending_sync_count || queue.length}</div>
            <div>
              <div className="text-sm text-slate-300">Pending Sync Items</div>
              <div className="text-xs text-slate-500">Queued updates waiting for network</div>
            </div>
            <button onClick={sync} disabled={syncing || status?.offline_mode} className="ml-auto btn-success flex items-center gap-2 text-sm">
              {syncing ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Upload className="w-4 h-4" />}
              Sync Now
            </button>
          </div>
          {queue.length > 0 ? (
            <div className="table-wrapper max-h-48 overflow-y-auto">
              <table className="table text-xs">
                <thead><tr><th>Route</th><th>Stop</th><th>Type</th><th>Driver</th><th>Queued</th></tr></thead>
                <tbody>
                  {queue.map(item => (
                    <tr key={item.id}>
                      <td className="font-mono">{item.route_id}</td>
                      <td className="font-mono">{item.stop_id}</td>
                      <td><span className="badge bg-amber-950 text-amber-300 border-amber-800">{item.update_type}</span></td>
                      <td>{item.driver_id}</td>
                      <td className="text-slate-500">{new Date(item.queued_at).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-6 text-slate-500 text-sm">
              <CheckCircle2 className="w-5 h-5 mx-auto mb-2 text-emerald-400" />
              No pending sync items
            </div>
          )}
        </div>

        {/* Manual Stop Update */}
        <div className="card">
          <h2 className="section-title">Manual Stop Update</h2>
          <p className="text-slate-400 text-sm mb-4">Submit a manual update when GPS is unavailable. Will be queued if offline.</p>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Route ID</label>
                <input type="text" value={manualForm.route_id} onChange={e => setManualForm(f => ({ ...f, route_id: e.target.value }))}
                  className="input w-full" placeholder="e.g. R001" />
              </div>
              <div>
                <label className="label">Stop ID</label>
                <input type="text" value={manualForm.stop_id} onChange={e => setManualForm(f => ({ ...f, stop_id: e.target.value }))}
                  className="input w-full" placeholder="e.g. S001" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Update Type</label>
                <select className="select w-full" value={manualForm.update_type} onChange={e => setManualForm(f => ({ ...f, update_type: e.target.value }))}>
                  <option value="arrived">Arrived</option>
                  <option value="departed">Departed</option>
                  <option value="student_count">Student Count</option>
                  <option value="delay">Delay</option>
                </select>
              </div>
              <div>
                <label className="label">Actual Time</label>
                <input type="time" value={manualForm.actual_time} onChange={e => setManualForm(f => ({ ...f, actual_time: e.target.value }))}
                  className="input w-full" />
              </div>
            </div>
            <div>
              <label className="label">Students Boarded</label>
              <input type="number" min={0} max={60} value={manualForm.student_count}
                onChange={e => setManualForm(f => ({ ...f, student_count: Number(e.target.value) }))}
                className="input w-full" />
            </div>
            <button onClick={submitManual} disabled={submitting || !manualForm.route_id || !manualForm.stop_id}
              className="btn-primary w-full flex items-center justify-center gap-2">
              {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Send className="w-4 h-4" />}
              {status?.offline_mode ? 'Queue Update (Offline Mode)' : 'Submit Update'}
            </button>
            {status?.offline_mode && (
              <div className="p-2 bg-amber-950 border border-amber-800 rounded-lg text-amber-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-3 h-3" />Network is offline — update will be queued for sync when connectivity returns.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Event log */}
      <div className="card">
        <h2 className="section-title">Fallback Event History</h2>
        {events.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">No fallback events recorded.</div>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead><tr><th>Type</th><th>Triggered By</th><th>Mode</th><th>Description</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                {events.slice(0, 20).map(ev => (
                  <tr key={ev.id}>
                    <td><span className="badge bg-slate-800 text-slate-300 border-slate-600">{ev.event_type}</span></td>
                    <td>{ev.triggered_by}</td>
                    <td><span className="badge bg-amber-950 text-amber-300 border-amber-800">{ev.fallback_mode}</span></td>
                    <td className="text-xs text-slate-400 max-w-xs truncate">{ev.description}</td>
                    <td>
                      {ev.resolved
                        ? <span className="badge-pass flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />Resolved</span>
                        : <span className="badge-fail flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Active</span>}
                    </td>
                    <td className="text-xs text-slate-500">{new Date(ev.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
