import { useEffect, useState } from 'react'
import api from '../api/client'
import Nav from '../components/Nav'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function Predictions() {
  const [stations, setStations] = useState([])
  const [sel, setSel] = useState('Times_Sq_42St')
  const [fc, setFc] = useState([])
  const [rec, setRec] = useState(null)
  const [peak, setPeak] = useState([])
  useEffect(() => { api.get('/api/stations').then((r) => { setStations(r.data); if (r.data[0]) setSel(r.data[0].code) }).catch(() => {}) }, [])
  useEffect(() => {
    if (!sel) return
    api.get(`/api/predictions/crowd?station_code=${sel}&hours=24`).then((r) => setFc(r.data.forecast)).catch(() => {})
    api.get(`/api/predictions/recommendations?station_code=${sel}&hours=6`).then((r) => setRec(r.data)).catch(() => {})
    api.get(`/api/predictions/peak-hours?station_code=${sel}`).then((r) => setPeak(r.data.peak_hours)).catch(() => {})
  }, [sel])
  return (
    <div><Nav />
      <div className="p-4 space-y-4">
        <div className="card flex gap-3 items-center flex-wrap"><b>AI predictions</b>
          <select className="input max-w-xs" value={sel} onChange={(e) => setSel(e.target.value)}>
            {stations.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </select>
          <span className="text-sm text-slate-400">RandomForest · lag + calendar features · R² ≈ 0.93</span></div>
        <div className="card"><h3 className="font-bold mb-2">24h crowd forecast</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={fc}><XAxis dataKey="timestamp" tick={false} /><YAxis /><Tooltip /><Legend />
              <Line type="monotone" dataKey="predicted_entries" stroke="#818cf8" dot={false} />
              <Line type="monotone" dataKey="predicted_total" stroke="#f43f5e" dot={false} />
            </LineChart>
          </ResponsiveContainer></div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card"><h3 className="font-bold mb-2">Peak hours</h3>
            {peak.map((p) => <div key={p.hour} className="text-sm py-1 border-b border-slate-800">{String(p.hour).padStart(2, '0')}:00 — avg {p.avg_total} pax ({p.congestion})</div>)}</div>
          <div className="card"><h3 className="font-bold mb-2">Smart recommendations</h3>
            <div className="text-sm text-indigo-300 mb-2">{rec?.summary}</div>
            {rec?.recommendations?.map((r) => <div key={r.timestamp} className="text-sm py-1 border-b border-slate-800">{String(r.timestamp).slice(11, 16)} · {Math.round(r.predicted_total)} pax → every {r.frequency_min} min · {r.action}</div>)}</div>
        </div>
      </div></div>
  )
}
