import { useEffect, useState } from 'react'
import api, { canOperate } from '../api/client'
import Nav from '../components/Nav'

export default function Scheduling() {
  const [rows, setRows] = useState([])
  const [opt, setOpt] = useState([])
  const staff = canOperate()
  const load = () => {
    api.get('/api/schedules').then((r) => setRows(r.data)).catch(() => {})
    api.get('/api/schedules/optimize').then((r) => setOpt(r.data)).catch(() => {})
  }
  useEffect(load, [])
  const delay = async (id) => {
    const v = prompt('Delay minutes?', '10')
    if (v == null) return
    await api.post(`/api/schedules/${id}/delay?delay_min=${v}`)
    load()
  }
  return (
    <div><Nav />
      <div className="p-4 grid gap-4 md:grid-cols-2">
        <div className="card"><h3 className="font-bold mb-2">Frequency optimization (AI)</h3>
          <div className="space-y-2 max-h-[70vh] overflow-auto">
            {opt.map((o) => (
              <div key={o.station_code} className="p-2 rounded-xl bg-slate-800 flex justify-between text-sm">
                <div><b>{o.station_name}</b> <span className="text-slate-400">· Line {o.line}</span><br />
                  <span className="text-slate-300">Load {(o.load_factor * 100).toFixed(0)}% → every {o.frequency_min} min ({o.trains_per_hour}/h) — {o.action}</span></div>
                <span className={`h-fit px-2 py-0.5 rounded-full text-xs border badge-${o.congestion}`}>{o.congestion}</span>
              </div>))}
          </div></div>
        <div className="card"><h3 className="font-bold mb-2">Timetable & delays</h3>
          {!staff && <p className="text-xs text-slate-400 mb-2">👁 Read-only passenger view — operators can report delays.</p>}
          <div className="space-y-2 max-h-[70vh] overflow-auto">
            {rows.map((s) => (
              <div key={s.id} className="p-2 rounded-xl bg-slate-800 text-sm flex justify-between items-center">
                <div>Line <b>{s.line}</b> · {s.station_code} · {s.departure} · every {s.frequency_min}m · <i>{s.status}{s.delay_min ? ` +${s.delay_min}m` : ''}</i></div>
                {staff && <button onClick={() => delay(s.id)} className="px-2 py-1 rounded bg-amber-600 text-xs">Delay</button>}
              </div>))}
          </div></div>
      </div></div>
  )
}
