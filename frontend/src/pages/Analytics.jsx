import { useEffect, useState } from 'react'
import api from '../api/client'
import Nav from '../components/Nav'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Analytics() {
  const [perf, setPerf] = useState([])
  const [op, setOp] = useState(null)
  useEffect(() => {
    api.get('/api/analytics/station-performance').then((r) => setPerf(r.data)).catch(() => {})
    api.get('/api/analytics/operational').then((r) => setOp(r.data)).catch(() => {})
  }, [])
  return (
    <div><Nav />
      <div className="p-4 space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          {[['Trips', op?.scheduled_trips], ['Delayed', op?.delayed_trips], ['Delay rate %', op?.delay_rate_pct], ['On-time %', op?.on_time_pct]].map(([k, v]) => (
            <div key={k} className="card"><div className="text-xs text-slate-400">{k}</div><div className="text-2xl font-bold">{v ?? '–'}</div></div>))}
        </div>
        <div className="card"><h3 className="font-bold mb-2">Station performance (total pax)</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={perf.slice(0, 12)}><XAxis dataKey="station_code" tick={false} /><YAxis /><Tooltip />
              <Bar dataKey="total_pax" fill="#818cf8" /></BarChart>
          </ResponsiveContainer></div>
        <div className="card"><h3 className="font-bold mb-2">Reports</h3>
          <table className="w-full text-sm"><thead><tr className="text-left text-slate-400"><th>Station</th><th>Total</th><th>Avg/h</th><th>Congestion</th></tr></thead>
            <tbody>{perf.map((p) => <tr key={p.station_code} className="border-t border-slate-800"><td>{p.station_name}</td><td>{p.total_pax}</td><td>{p.avg_per_hour}</td><td>{p.congestion}</td></tr>)}</tbody></table></div>
      </div></div>
  )
}
