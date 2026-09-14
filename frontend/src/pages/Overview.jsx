import { useEffect, useState } from 'react'
import api from '../api/client'
import Nav from '../components/Nav'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

export default function Overview() {
  const [kpis, setKpis] = useState(null)
  const [heat, setHeat] = useState([])
  const [traffic, setTraffic] = useState([])
  useEffect(() => {
    api.get('/api/analytics/kpis').then((r) => setKpis(r.data)).catch(() => {})
    api.get('/api/crowd/heatmap').then((r) => setHeat(r.data)).catch(() => {})
    api.get('/api/analytics/traffic').then((r) => setTraffic(r.data.hourly.slice(-48))).catch(() => {})
  }, [])
  return (
    <div><Nav />
      <div className="p-4 grid gap-4 md:grid-cols-4">
        {[
          ['Scheduled trips', kpis?.scheduled_trips ?? '–'],
          ['On-time %', kpis?.on_time_pct ?? '–'],
          ['Critical alerts', kpis?.critical_alerts ?? '–'],
          ['Top station', kpis?.top_station?.station_name ?? '–'],
        ].map(([k, v]) => <div key={k} className="card"><div className="text-xs text-slate-400">{k}</div><div className="text-2xl font-bold">{v}</div></div>)}
      </div>
      <div className="p-4 grid gap-4 md:grid-cols-2">
        <div className="card"><h3 className="font-bold mb-2">Network traffic (last 48h)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={traffic}><XAxis dataKey="timestamp" tick={false} /><YAxis /><Tooltip /><Line type="monotone" dataKey="total" stroke="#818cf8" dot={false} /></LineChart>
          </ResponsiveContainer></div>
        <div className="card"><h3 className="font-bold mb-2">Congestion heatmap (live)</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {heat.map((h) => (
              <div key={h.station_code} className={`p-2 rounded-xl border ${h.congestion === 'critical' ? 'bg-red-600/20 border-red-500' : h.congestion === 'high' ? 'bg-orange-600/20 border-orange-500' : h.congestion === 'medium' ? 'bg-amber-600/10 border-amber-500/50' : 'bg-emerald-600/10 border-emerald-600/40'}`}>
                <div className="text-xs font-bold truncate">{h.station_name}</div>
                <div className="text-lg font-black">{h.total}</div>
                <div className="text-[11px] uppercase">{h.congestion}</div>
              </div>))}
          </div></div>
      </div></div>
  )
}
