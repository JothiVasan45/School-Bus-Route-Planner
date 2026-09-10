import { useState } from 'react'
import { reportsApi } from '../api/client'
import { FileText, Download, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Reports() {
  const [loading, setLoading] = useState<string | null>(null)
  const [jsonData, setJsonData] = useState<any>(null)

  const download = async (format: 'json' | 'html' | 'pdf') => {
    setLoading(format)
    try {
      const res = await reportsApi.evaluation(format)
      if (format === 'json') {
        setJsonData(res.data)
        toast.success('Report data loaded')
      } else {
        const blob = new Blob([res.data], { type: format === 'html' ? 'text/html' : 'application/pdf' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `evaluation_report.${format}`
        a.click()
        window.URL.revokeObjectURL(url)
        toast.success(`${format.toUpperCase()} report downloaded`)
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Report generation failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Evaluation Reports</h1>
        <p className="text-slate-400 text-sm mt-1">Generate and download comprehensive evaluation reports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { format: 'json', title: 'JSON Report', icon: '{ }', color: 'bg-primary-700', desc: 'Raw structured data. View inline below or export for programmatic processing.' },
          { format: 'html', title: 'HTML Report', icon: '🌐', color: 'bg-purple-700', desc: 'Full styled HTML evaluation report with tables, charts, and stakeholder validation summary.' },
          { format: 'pdf', title: 'PDF Report', icon: '📄', color: 'bg-red-700', desc: 'Formatted PDF report for submission. Requires reportlab. Falls back to HTML if unavailable.' },
        ].map(r => (
          <div key={r.format} className="card flex flex-col">
            <div className={`w-12 h-12 ${r.color} rounded-xl flex items-center justify-center text-white text-xl font-mono mb-4`}>{r.icon}</div>
            <h2 className="text-lg font-semibold text-white mb-1">{r.title}</h2>
            <p className="text-slate-400 text-sm flex-1 mb-4">{r.desc}</p>
            <button onClick={() => download(r.format as any)} disabled={loading === r.format}
              className="btn-primary flex items-center justify-center gap-2">
              {loading === r.format
                ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                : <Download className="w-4 h-4" />}
              {r.format === 'json' ? 'Load JSON' : `Download ${r.format.toUpperCase()}`}
            </button>
          </div>
        ))}
      </div>

      {jsonData && (
        <div className="card animate-slide-up">
          <h2 className="section-title">Report Summary (JSON)</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Baseline Routes', val: jsonData.baseline?.n_routes || 'N/A' },
              { label: 'Optimized Routes', val: jsonData.optimized?.n_routes || 'N/A' },
              { label: 'Experiments Run', val: jsonData.experiments || 'N/A' },
              { label: 'Avg Satisfaction', val: jsonData.avg_satisfaction ? `${jsonData.avg_satisfaction}/5.0` : 'N/A' },
            ].map(item => (
              <div key={item.label} className="card-sm text-center">
                <div className="text-2xl font-bold text-white">{item.val}</div>
                <div className="text-xs text-slate-400">{item.label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {['baseline', 'optimized'].map(type => {
              const d = jsonData[type]
              if (!d || !d.n_routes) return null
              return (
                <div key={type}>
                  <h3 className="text-sm font-semibold capitalize text-slate-300 mb-3">{type} ({d.n_routes} routes)</h3>
                  <div className="space-y-2">
                    {[
                      { label: 'Total Distance', val: `${d.total_distance_km} km` },
                      { label: 'Avg Duration', val: `${d.avg_duration_min} min` },
                      { label: 'On-Time %', val: `${d.avg_on_time_pct}%` },
                      { label: 'Capacity Violations', val: d.capacity_violations },
                      { label: 'Time Window Violations', val: d.tw_violations },
                      { label: 'Avg Reliability %', val: `${d.avg_reliability_pct}%` },
                    ].map(row => (
                      <div key={row.label} className="flex justify-between py-1.5 border-b border-border/30 last:border-0">
                        <span className="text-slate-400 text-sm">{row.label}</span>
                        <span className="text-white font-semibold text-sm">{row.val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>

          <details className="mt-4">
            <summary className="text-sm text-slate-400 cursor-pointer hover:text-slate-200">View raw JSON data</summary>
            <pre className="mt-3 p-4 bg-slate-900 rounded-lg text-xs text-emerald-300 overflow-auto max-h-64 font-mono">
              {JSON.stringify(jsonData, null, 2)}
            </pre>
          </details>
        </div>
      )}

      <div className="card">
        <h2 className="section-title">Report Contents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-300">
          {[
            '1. Problem Statement and Background',
            '2. Dataset Summary (stops, students, buses, drivers)',
            '3. Optimization Methods (Baseline + Multi-Objective)',
            '4. Baseline vs Optimized Results Table',
            '5. Failure Cases Tested (GPS, Network, Capacity, etc.)',
            '6. Stakeholder Validation Summary',
            '7. Override Audit Log Statistics',
            '8. Known Limitations and Assumptions',
            '9. Future Improvement Directions',
            '10. Conclusion and Findings',
          ].map(item => (
            <div key={item} className="flex items-start gap-2">
              <span className="text-primary-400 mt-0.5">•</span>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
