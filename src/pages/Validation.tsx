import { useState, useEffect } from 'react'
import { validationApi } from '../api/client'
import { MessageSquare, Send, Star, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'

const QUESTIONS = [
  { key: 'q1_route_clarity', label: 'Route Clarity', desc: 'Routes are clearly presented with stop sequences and timings.' },
  { key: 'q2_operational_realism', label: 'Operational Realism', desc: 'The constraints and scenarios reflect real operational challenges.' },
  { key: 'q3_workload_useful', label: 'Workload Analysis', desc: 'The driver workload display helps identify fairness issues.' },
  { key: 'q4_comparison_useful', label: 'Comparison Value', desc: 'The baseline vs optimized comparison provides useful insights.' },
  { key: 'q5_fallback_clear', label: 'Fallback Handling', desc: 'The offline/fallback mode behaves as expected in failure scenarios.' },
  { key: 'q6_would_use_daily', label: 'Daily Usability', desc: 'I would use this system for daily transportation planning.' },
]

function StarRating({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hovered, setHovered] = useState(0)
  return (
    <div className="flex gap-1">
      {[1,2,3,4,5].map(star => (
        <button key={star} type="button"
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          onClick={() => onChange(star)}
          className="transition-transform hover:scale-110">
          <Star className={`w-7 h-7 transition-colors ${(hovered || value) >= star ? 'text-amber-400 fill-amber-400' : 'text-slate-600'}`} />
        </button>
      ))}
    </div>
  )
}

const DEMO_RESPONSES = [
  { name: 'Ravi K, Senior Transportation Planner', q1: 5, q2: 4, q3: 5, q4: 5, q5: 4, q6: 4, overall: 4.5 },
  { name: 'Priya S, School Administrator', q1: 4, q2: 5, q3: 4, q4: 5, q5: 3, q6: 4, overall: 4.2 },
  { name: 'Muthu R, Fleet Manager', q1: 5, q2: 5, q3: 5, q4: 4, q5: 5, q6: 5, overall: 4.8 },
  { name: 'Anitha V, Driver Supervisor', q1: 4, q2: 4, q3: 5, q4: 4, q5: 4, q6: 5, overall: 4.3 },
  { name: 'Dr. Lakshmi P, Head of Operations', q1: 5, q2: 5, q3: 4, q4: 5, q5: 4, q6: 5, overall: 4.7 },
]

export default function Validation() {
  const [form, setForm] = useState({
    respondent_name: '', respondent_role: 'planner',
    q1_route_clarity: 0, q2_operational_realism: 0, q3_workload_useful: 0,
    q4_comparison_useful: 0, q5_fallback_clear: 0, q6_would_use_daily: 0,
    comments: '', is_simulated: true,
  })
  const [submitting, setSubmitting] = useState(false)
  const [summary, setSummary] = useState<any>(null)
  const [view, setView] = useState<'form' | 'summary'>('form')

  const loadSummary = async () => {
    try {
      const res = await validationApi.summary()
      setSummary(res.data)
    } catch {}
  }

  useEffect(() => { loadSummary() }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const scores = [form.q1_route_clarity, form.q2_operational_realism, form.q3_workload_useful,
                    form.q4_comparison_useful, form.q5_fallback_clear, form.q6_would_use_daily]
    if (scores.some(s => s === 0)) { toast.error('Please rate all questions.'); return }
    setSubmitting(true)
    try {
      await validationApi.submit(form)
      toast.success('Feedback submitted! Thank you.')
      await loadSummary()
      setView('summary')
      setForm(f => ({ ...f, respondent_name: '', comments: '', q1_route_clarity: 0, q2_operational_realism: 0, q3_workload_useful: 0, q4_comparison_useful: 0, q5_fallback_clear: 0, q6_would_use_daily: 0 }))
    } catch (e: any) {
      toast.error('Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const submitDemoResponses = async () => {
    for (const dr of DEMO_RESPONSES) {
      await validationApi.submit({
        respondent_name: dr.name, respondent_role: 'planner',
        q1_route_clarity: dr.q1, q2_operational_realism: dr.q2, q3_workload_useful: dr.q3,
        q4_comparison_useful: dr.q4, q5_fallback_clear: dr.q5, q6_would_use_daily: dr.q6,
        comments: 'Simulated stakeholder validation response.', is_simulated: true,
      })
    }
    toast.success('5 demo responses submitted.')
    await loadSummary()
    setView('summary')
  }

  const radarData = summary ? QUESTIONS.map(q => ({
    subject: q.label.split(' ')[0],
    score: (summary.question_averages?.[q.key] || 0) * 20,
  })) : []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Stakeholder Validation</h1>
          <p className="text-slate-400 text-sm mt-1">Prototype validation feedback from transportation planners and operators</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setView('form')} className={`px-4 py-2 rounded-lg text-sm transition-all ${view === 'form' ? 'bg-primary-600 text-white' : 'bg-slate-700 text-slate-300'}`}>Submit Feedback</button>
          <button onClick={() => { loadSummary(); setView('summary') }} className={`px-4 py-2 rounded-lg text-sm transition-all ${view === 'summary' ? 'bg-primary-600 text-white' : 'bg-slate-700 text-slate-300'}`}>View Summary</button>
        </div>
      </div>

      <div className="card border-amber-800/30 bg-amber-950/10 text-amber-300 text-sm flex items-start gap-3 py-3 px-4">
        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span><strong>Prototype Stakeholder Simulation:</strong> This is a simulated validation exercise for research/prototype evaluation. Real-world deployment and formal stakeholder evaluation has not occurred.</span>
      </div>

      {view === 'form' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="section-title">Feedback Form</h2>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Your Name (optional)</label>
                  <input type="text" value={form.respondent_name} onChange={e => setForm(f => ({...f, respondent_name: e.target.value}))}
                    className="input w-full" placeholder="Anonymous" />
                </div>
                <div>
                  <label className="label">Role</label>
                  <select className="select w-full" value={form.respondent_role} onChange={e => setForm(f => ({...f, respondent_role: e.target.value}))}>
                    <option value="planner">Transportation Planner</option>
                    <option value="driver">Bus Driver</option>
                    <option value="admin">Administrator</option>
                    <option value="researcher">Researcher</option>
                  </select>
                </div>
              </div>

              {QUESTIONS.map(q => (
                <div key={q.key} className="space-y-1">
                  <div className="text-sm font-medium text-slate-200">{q.label}</div>
                  <div className="text-xs text-slate-500 mb-2">{q.desc}</div>
                  <StarRating value={form[q.key as keyof typeof form] as number} onChange={v => setForm(f => ({...f, [q.key]: v}))} />
                </div>
              ))}

              <div>
                <label className="label">Comments (optional)</label>
                <textarea value={form.comments} onChange={e => setForm(f => ({...f, comments: e.target.value}))}
                  className="input w-full h-20 resize-none" placeholder="Any additional feedback..." />
              </div>

              <button type="submit" disabled={submitting} className="btn-primary w-full flex items-center justify-center gap-2">
                {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Send className="w-4 h-4" />}
                Submit Feedback
              </button>
            </form>
          </div>

          <div className="space-y-4">
            <div className="card">
              <h2 className="section-title">Simulated Stakeholder Responses</h2>
              <p className="text-slate-400 text-sm mb-4">Load pre-generated responses from 5 simulated stakeholders for demonstration purposes.</p>
              <div className="space-y-2 mb-4">
                {DEMO_RESPONSES.map(dr => (
                  <div key={dr.name} className="flex items-center justify-between py-2 border-b border-border/30">
                    <span className="text-sm text-slate-300">{dr.name}</span>
                    <div className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                      <span className="text-sm font-bold text-white">{dr.overall}</span>
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={submitDemoResponses} className="btn-secondary w-full flex items-center justify-center gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4" />Load 5 Demo Responses
              </button>
            </div>

            {summary && summary.n_responses > 0 && (
              <div className="card-sm text-center">
                <div className="text-4xl font-bold text-amber-400 mb-1">{summary.avg_overall_score}/5.0</div>
                <div className="text-slate-400 text-sm">Average Satisfaction Score</div>
                <div className="text-xs text-slate-500 mt-1">{summary.n_responses} total responses ({summary.n_simulated} simulated, {summary.n_real} real)</div>
              </div>
            )}
          </div>
        </div>
      )}

      {view === 'summary' && summary && (
        <div className="space-y-6 animate-slide-up">
          {summary.n_responses === 0 ? (
            <div className="card text-center py-12">
              <MessageSquare className="w-8 h-8 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">No feedback submitted yet. Submit feedback or load demo responses.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card-sm text-center"><div className="text-3xl font-bold text-amber-400">{summary.avg_overall_score}</div><div className="text-xs text-slate-400">Avg Score / 5.0</div></div>
                <div className="card-sm text-center"><div className="text-3xl font-bold text-white">{summary.n_responses}</div><div className="text-xs text-slate-400">Total Responses</div></div>
                <div className="card-sm text-center"><div className="text-3xl font-bold text-slate-400">{summary.n_simulated}</div><div className="text-xs text-slate-400">Simulated</div></div>
                <div className="card-sm text-center"><div className="text-3xl font-bold text-primary-400">{summary.n_real}</div><div className="text-xs text-slate-400">Real</div></div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                  <h2 className="section-title">Question Averages</h2>
                  <div className="space-y-3">
                    {QUESTIONS.map(q => {
                      const score = summary.question_averages?.[q.key] || 0
                      return (
                        <div key={q.key} className="flex items-center gap-3">
                          <div className="text-sm text-slate-300 w-36 flex-shrink-0">{q.label}</div>
                          <div className="flex-1 progress-bar">
                            <div className={`progress-fill ${score >= 4.5 ? 'bg-emerald-500' : score >= 3.5 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${score * 20}%` }} />
                          </div>
                          <div className="text-sm font-bold text-white w-8">{score.toFixed(1)}</div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="card">
                  <h2 className="section-title">Radar: Question Scores</h2>
                  <ResponsiveContainer width="100%" height={260}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Radar name="Score" dataKey="score" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card">
                <h2 className="section-title">Individual Responses</h2>
                <div className="space-y-3">
                  {summary.responses?.slice(0, 10).map((r: any, i: number) => (
                    <div key={i} className="p-3 rounded-lg bg-slate-800/30 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">{r.respondent_name || 'Anonymous'}</span>
                        <div className="flex items-center gap-2">
                          {r.is_simulated && <span className="badge bg-slate-800 text-slate-400 border-slate-600 text-xs">SIMULATED</span>}
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                            <span className="font-bold text-white text-sm">{r.overall_score}</span>
                          </div>
                        </div>
                      </div>
                      {r.comments && <p className="text-xs text-slate-400 italic">"{r.comments}"</p>}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
