import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api, { login } from '../api/client'

export function Login() {
  const [u, setU] = useState('admin')
  const [p, setP] = useState('admin123')
  const [err, setErr] = useState('')
  const nav = useNavigate()
  const go = async (e) => {
    e.preventDefault()
    try {
      const r = await login(u, p)
      localStorage.setItem('token', r.data.access_token)
      const me = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${r.data.access_token}` },
      })
      localStorage.setItem('role', me.data.role)
      localStorage.setItem('username', me.data.username)
      nav('/')
    } catch { setErr('Login failed. Backend running? Default admin/admin123.') }
  }
  return (
    <div className="min-h-screen grid place-items-center p-4">
      <form onSubmit={go} className="card w-full max-w-sm space-y-3">
        <h1 className="text-2xl font-black">🚇 MetroFlow AI</h1>
        <p className="text-sm text-slate-400">NYC Subway crowd intelligence · admin/admin123</p>
        <input className="input" value={u} onChange={(e) => setU(e.target.value)} placeholder="username" />
        <input className="input" type="password" value={p} onChange={(e) => setP(e.target.value)} placeholder="password" />
        {err && <div className="text-red-400 text-sm">{err}</div>}
        <button className="btn w-full">Login</button>
      </form>
    </div>
  )
}

export function Guard({ children }) {
  if (!localStorage.getItem('token'))
    return <div className="p-8">Not logged in. <Link className="underline" to="/login">Login</Link></div>
  // Backfill role for sessions created before role-gating (then re-render)
  const [ready, setReady] = useState(!!localStorage.getItem('role'))
  useEffect(() => {
    if (!localStorage.getItem('role')) {
      api.get('/api/auth/me').then((r) => {
        localStorage.setItem('role', r.data.role)
        localStorage.setItem('username', r.data.username)
        setReady(true)
      }).catch(() => { localStorage.removeItem('token'); setReady(true) })
    }
  }, [])
  if (!ready) return <div className="p-8">Loading…</div>
  return children
}
