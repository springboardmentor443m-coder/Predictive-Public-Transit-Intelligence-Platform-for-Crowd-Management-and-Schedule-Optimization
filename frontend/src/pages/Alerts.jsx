import { useEffect, useState } from 'react'
import api, { canOperate } from '../api/client'
import Nav from '../components/Nav'

export default function Alerts() {
  const [rows, setRows] = useState([])
  const staff = canOperate()
  const [form, setForm] = useState({ type: 'overcrowding', severity: 'high', station_code: '', message: '' })
  const load = () => api.get('/api/alerts').then((r) => setRows(r.data)).catch(() => {})
  useEffect(() => {
    load()
    const wsProto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${wsProto}://${location.host}/api/alerts/ws/alerts`)
    ws.onmessage = () => load()
    const t = setInterval(load, 10000)
    return () => { try { ws.close() } catch {} clearInterval(t) }
  }, [])
  const send = async (e) => {
    e.preventDefault()
    await api.post('/api/alerts', { ...form, station_code: form.station_code || null })
    setForm({ ...form, message: '' })
    load()
  }
  return (
    <div><Nav />
      <div className={`p-4 grid gap-4 ${staff ? 'md:grid-cols-2' : ''}`}>
        {staff && (
        <div className="card"><h3 className="font-bold mb-2">Broadcast alert / emergency</h3>
          <form onSubmit={send} className="space-y-2">
            <div className="flex gap-2">
              <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option>overcrowding</option><option>delay</option><option>emergency</option><option>info</option>
              </select>
              <select className="input" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                <option>low</option><option>medium</option><option>high</option><option>critical</option>
              </select></div>
            <input className="input" placeholder="station_code (optional)" value={form.station_code} onChange={(e) => setForm({ ...form, station_code: e.target.value })} />
            <textarea className="input" placeholder="message" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
            <button className="btn w-full">Send alert</button>
          </form></div>
        )}
        <div className="card"><h3 className="font-bold mb-2">Live service alerts</h3>
          {!staff && <p className="text-xs text-slate-400 mb-2">👁 Read-only passenger view.</p>}
          <div className="space-y-2 max-h-[70vh] overflow-auto">
            {rows.map((a) => (
              <div key={a.id} className="p-2 rounded-xl bg-slate-800 text-sm">
                <b>[{a.severity}] {a.type}</b> {a.station_code ? `@ ${a.station_code}` : ''}<br />{a.message}
                <div className="text-xs text-slate-400">{a.created_at}</div>
              </div>))}
            {!rows.length && <div className="text-slate-400 text-sm">No alerts yet.</div>}
          </div></div>
      </div></div>
  )
}
