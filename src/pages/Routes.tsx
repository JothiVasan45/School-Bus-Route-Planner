import { useEffect, useState, useRef } from 'react'
import { optimizationApi, dataApi } from '../api/client'
import { MapPin, Bus, Clock, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

// Leaflet dynamic import to avoid SSR issues
let L: any = null

function RouteMap({ routes, stops }: { routes: any[]; stops: any[] }) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<any>(null)

  useEffect(() => {
    if (!mapRef.current || routes.length === 0) return
    import('leaflet').then(leaflet => {
      L = leaflet.default
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
      }
      const map = L.map(mapRef.current!, { zoomControl: true })
      mapInstanceRef.current = map

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 18,
      }).addTo(map)

      const stopMap: Record<string, any> = {}
      stops.forEach(s => { stopMap[s.stop_id] = s })

      const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#14b8a6']
      const bounds: any[] = []

      routes.forEach((route, ridx) => {
        const color = colors[ridx % colors.length]
        const latlngs: [number, number][] = []

        route.stops?.forEach((rs: any, i: number) => {
          const stop = stopMap[rs.stop_id]
          if (!stop) return
          latlngs.push([stop.latitude, stop.longitude])
          bounds.push([stop.latitude, stop.longitude])

          const icon = L.divIcon({
            html: `<div style="
              background:${color};border:2px solid white;border-radius:50%;
              width:24px;height:24px;display:flex;align-items:center;justify-content:center;
              color:white;font-size:10px;font-weight:bold;
              box-shadow:0 2px 6px rgba(0,0,0,0.4);">${i + 1}</div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            className: '',
          })

          L.marker([stop.latitude, stop.longitude], { icon })
            .addTo(map)
            .bindPopup(`
              <div style="min-width:200px">
                <b>${stop.stop_name}</b><br/>
                <span style="color:#94a3b8;font-size:12px">Stop ${rs.stop_id} • Seq #${i + 1}</span><br/>
                ${rs.planned_arrival ? `<span style="font-size:12px">Arrival: <b>${rs.planned_arrival}</b></span><br/>` : ''}
                ${rs.window_start ? `<span style="font-size:12px">Window: ${rs.window_start}–${rs.window_end}</span>` : ''}
                ${rs.window_violated ? '<br/><span style="color:#ef4444;font-size:11px">⚠ TIME WINDOW VIOLATED</span>' : ''}
              </div>
            `)
        })

        if (latlngs.length > 1) {
          L.polyline(latlngs, { color, weight: 3, opacity: 0.8, dashArray: '6 4' }).addTo(map)
        }
      })

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30] })
      } else {
        map.setView([13.06, 80.22], 12)
      }
    })
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [routes, stops])

  return <div ref={mapRef} className="w-full h-full rounded-xl" />
}

export default function Routes() {
  const [routes, setRoutes] = useState<any[]>([])
  const [stops, setStops] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRoute, setSelectedRoute] = useState<any>(null)
  const [filter, setFilter] = useState<'all' | 'baseline' | 'multiobjective'>('all')

  useEffect(() => {
    const load = async () => {
      try {
        const [rRes, sRes] = await Promise.all([
          optimizationApi.list(filter === 'all' ? undefined : filter),
          dataApi.stops(),
        ])
        setRoutes(rRes.data)
        setStops(sRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [filter])

  const displayRoutes = routes.slice(0, 20)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Route Map</h1>
          <p className="text-slate-400 text-sm mt-1">Interactive route visualization with stop sequences, time windows, and assignments</p>
        </div>
        <div className="flex gap-2">
          {(['all', 'baseline', 'multiobjective'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg capitalize transition-all ${filter === f ? 'bg-primary-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
              {f === 'all' ? 'All Routes' : f === 'baseline' ? 'Baseline' : 'Optimized'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Map */}
        <div className="xl:col-span-2 card p-0 overflow-hidden" style={{ height: '520px' }}>
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-500">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p>Loading map...</p>
              </div>
            </div>
          ) : routes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-500">
              <div className="text-center">
                <MapPin className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p>No routes found. Run optimization first.</p>
              </div>
            </div>
          ) : (
            <RouteMap routes={selectedRoute ? [selectedRoute] : displayRoutes} stops={stops} />
          )}
        </div>

        {/* Route list */}
        <div className="card overflow-y-auto" style={{ maxHeight: '520px' }}>
          <h2 className="section-title">Routes ({routes.length})</h2>
          <div className="space-y-2">
            {displayRoutes.map((route, i) => {
              const isSelected = selectedRoute?.route_id === route.route_id
              const colors = ['blue', 'emerald', 'amber', 'purple', 'red', 'cyan', 'pink', 'lime']
              const color = colors[i % colors.length]
              return (
                <div
                  key={route.route_id}
                  onClick={() => setSelectedRoute(isSelected ? null : route)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected ? 'border-primary-500 bg-primary-950/30' : 'border-slate-700 bg-slate-800/30 hover:border-slate-500'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full bg-${color}-500 flex-shrink-0`} />
                      <span className="text-sm font-semibold text-white">Route {i + 1}</span>
                      <span className={`badge ${route.optimization_type === 'baseline' ? 'bg-slate-800 text-slate-400 border-slate-700' : 'bg-primary-950 text-primary-300 border-primary-800'} text-xs`}>
                        {route.optimization_type === 'baseline' ? 'BASE' : 'OPT'}
                      </span>
                    </div>
                    {route.capacity_violations > 0 && <AlertTriangle className="w-4 h-4 text-red-400" />}
                    {route.capacity_violations === 0 && route.time_window_violations === 0 && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  </div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-400">
                    <span><Bus className="w-3 h-3 inline mr-1" />{route.bus_id}</span>
                    <span><MapPin className="w-3 h-3 inline mr-1" />{route.stop_count} stops</span>
                    <span>{route.total_distance_km?.toFixed(1)} km</span>
                    <span className="text-emerald-400">{(route.on_time_probability * 100)?.toFixed(0)}% OTP</span>
                    <span className="text-primary-400">{route.total_students} students</span>
                    <span className="font-mono">{route.planned_start}–{route.planned_end}</span>
                  </div>
                  {(route.capacity_violations > 0 || route.time_window_violations > 0) && (
                    <div className="mt-2 flex gap-2">
                      {route.capacity_violations > 0 && <span className="badge-fail">CAP VIOL</span>}
                      {route.time_window_violations > 0 && <span className="badge-warning">TW VIOL</span>}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Selected route details */}
      {selectedRoute && (
        <div className="card animate-slide-up">
          <h2 className="section-title">Route Detail — {selectedRoute.route_id}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {[
              { l: 'Bus', v: selectedRoute.bus_id },
              { l: 'Driver', v: selectedRoute.driver_id },
              { l: 'Distance', v: `${selectedRoute.total_distance_km?.toFixed(1)} km` },
              { l: 'Duration', v: `${selectedRoute.total_duration_minutes?.toFixed(0)} min` },
              { l: 'Students', v: `${selectedRoute.total_students} / ${selectedRoute.capacity_limit}` },
              { l: 'On-Time Prob.', v: `${(selectedRoute.on_time_probability * 100)?.toFixed(1)}%` },
              { l: 'Reliability', v: `${(selectedRoute.reliability_score * 100)?.toFixed(1)}%` },
              { l: 'P90 Duration', v: `${selectedRoute.p90_duration?.toFixed(0)} min` },
            ].map(item => (
              <div key={item.l} className="metric-row flex-col items-start gap-1">
                <span className="metric-label">{item.l}</span>
                <span className="metric-value text-sm">{item.v}</span>
              </div>
            ))}
          </div>
          <h3 className="text-sm font-semibold text-slate-300 mb-2">Stop Sequence</h3>
          <div className="overflow-x-auto">
            <table className="table text-xs">
              <thead>
                <tr>
                  <th>#</th><th>Stop ID</th><th>Arrival</th><th>Departure</th><th>Window</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {selectedRoute.stops?.map((rs: any) => (
                  <tr key={rs.stop_id}>
                    <td className="font-bold">{rs.sequence + 1}</td>
                    <td className="font-mono">{rs.stop_id}</td>
                    <td className="font-mono">{rs.planned_arrival}</td>
                    <td className="font-mono">{rs.planned_departure}</td>
                    <td className="font-mono">{rs.window_start}–{rs.window_end}</td>
                    <td>
                      {rs.window_violated
                        ? <span className="badge-fail">VIOLATED</span>
                        : <span className="badge-pass">OK</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {selectedRoute.notes && (
            <div className="mt-3 p-3 bg-primary-950/30 border border-primary-800/40 rounded-lg text-sm text-primary-200">
              <Info className="w-4 h-4 inline mr-2" />{selectedRoute.notes}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
