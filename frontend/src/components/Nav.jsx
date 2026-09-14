import { Link, useNavigate } from 'react-router-dom'
import { logout, getRole, getUsername } from '../api/client'

export default function Nav() {
  const nav = useNavigate()
  const out = () => { logout(); nav('/login') }
  const role = getRole()
  const links = [
    ['/', 'Overview'], ['/crowd', 'Crowd'], ['/scheduling', 'Scheduling'],
    ['/predictions', 'AI Predictions'], ['/alerts', 'Alerts'], ['/analytics', 'Analytics'],
  ]
  return (
    <nav className="flex flex-wrap gap-2 items-center justify-between p-4 border-b border-slate-800 bg-slate-900/60 sticky top-0 z-10">
      <div className="font-black text-xl">🚇 MetroFlow <span className="text-indigo-400">AI</span></div>
      <div className="flex gap-2 flex-wrap items-center">
        {links.map(([to, l]) => <Link key={to} className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm" to={to}>{l}</Link>)}
        <span title={getUsername()} className={`px-2 py-1 rounded-full text-xs border ${role === 'admin' ? 'badge-critical' : role === 'operator' ? 'badge-medium' : 'badge-low'}`}>{role}</span>
        <button onClick={out} className="px-3 py-1.5 rounded-lg bg-red-600/80 text-sm">Logout</button>
      </div>
    </nav>
  )
}

export function CongBadge({ level }) {
  return <span className={`px-2 py-0.5 rounded-full text-xs border badge-${level}`}>{level}</span>
}
