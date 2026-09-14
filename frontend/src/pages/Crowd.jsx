import { useEffect, useState } from 'react'
import api from '../api/client'
import Nav, { CongBadge } from '../components/Nav'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function Crowd() {
  const [stations, setStations] = useState([])
  const [sel, setSel] = useState('Times_Sq_42St')
  const [hist, setHist] = useState([])
  const [io, setIo] = useState(null)
  useEffect(() => { api.get('/api/stations').then((r) => { setStations(r.data); if (r.data[0]) setSel(r.data[0].code) }).catch(() => {}) }, [])
  useEffect(() => {
    if (!sel) return
    api.get(`/api/crowd/history?station_code=${sel}&hours=72`).then((r) => setHist(r.data)).catch(() => {})
    api.get(`/api/crowd/inflow-outflow?station_code=${sel}&hours=24`).then((r) => setIo(r.data)).catch(() => {})
  }, [sel])
  return (
    <div><Nav />
      <div className="p-4 space-y-4">
        <div className="card flex gap-3 items-center flex-wrap">
          <b>Crowd monitoring</b>
          <select className="input max-w-xs" value={sel} onChange={(e) => setSel(e.target.value)}>
            {stations.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </select>
          {io && <span className="text-sm text-slate-300">In {io.entries} · Out {io.exits} · Net {io.net_flow} ({io.direction})</span>}
        </div>
        <div className="card"><h3 className="font-bold mb-2">Entries / exits — last 72h</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hist}><XAxis dataKey="timestamp" tick={false} /><YAxis /><Tooltip /><Legend />
              <Line type="monotone" dataKey="entries" stroke="#22d3ee" dot={false} />
              <Line type="monotone" dataKey="exits" stroke="#f472b6" dot={false} />
              <Line type="monotone" dataKey="total" stroke="#a3e635" dot={false} />
            </LineChart>
          </ResponsiveContainer></div>
        <div className="card"><h3 className="font-bold mb-2">Hourly congestion</h3>
          <div className="flex gap-1 flex-wrap">{hist.slice(-48).map((h, i) => (
            <div key={i} title={`${h.timestamp} total ${h.total}`} className={`w-8 h-8 grid place-items-center rounded text-[10px] border badge-${h.congestion}`}>{h.total > 999 ? `${(h.total / 1000).toFixed(1)}k` : h.total}</div>))}
          </div></div>
      </div></div>
  )
}
