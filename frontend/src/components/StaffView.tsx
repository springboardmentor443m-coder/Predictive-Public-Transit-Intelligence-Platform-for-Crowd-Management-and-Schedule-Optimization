import React, { useEffect, useState } from 'react';
import { Shield, UserPlus, Users, CheckCircle, Lock, BadgeCheck, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface StaffViewProps {
  currentUser: User | null;
}

export const StaffView: React.FC<StaffViewProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // New user form state
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<'operator' | 'admin'>('operator');
  const [newTitle, setNewTitle] = useState('Line Dispatcher');
  const [newBadge, setNewBadge] = useState('NY-OPS-99');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      const data = await api.listUsers();
      setUsers(data);
    } catch (err) {
      console.error('Failed to list users', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.createUser({
        name: newName,
        email: newEmail,
        password: newPassword,
        role: newRole,
        title: newTitle,
        badge_id: newBadge
      });
      setSuccessMsg(`Created user account for ${newName} (${newRole.toUpperCase()})`);
      setShowAddModal(false);
      setNewName('');
      setNewEmail('');
      setNewPassword('');
      fetchUsers();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Creation failed');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Add Staff Action */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-purple-600/20 text-purple-400 rounded-2xl border border-purple-500/30">
            <Shield className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black text-white">User Management & Access Control</h2>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Admin Console
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Role-based access control (RBAC), operator directory, and security credential management.
            </p>
          </div>
        </div>

        {currentUser?.role === 'admin' && (
          <button
            onClick={() => setShowAddModal(true)}
            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-purple-600/20 flex items-center space-x-2 cursor-pointer"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add Transit Operator</span>
          </button>
        )}
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Role Privileges Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-purple-300 flex items-center space-x-2">
              <Shield className="w-4 h-4 text-purple-400" />
              <span>Admin Role Privileges</span>
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
              ROOT / DIRECTOR
            </span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5">
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-purple-400" />
              <span>Configure line schedules, baseline headway, and peak multipliers</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-purple-400" />
              <span>Broadcast system-wide high-priority emergency alerts</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-purple-400" />
              <span>Provision and manage rail operator credentials</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-purple-400" />
              <span>Trigger automated peak-hour schedule optimization</span>
            </li>
          </ul>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-blue-300 flex items-center space-x-2">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Operator Role Privileges</span>
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">
              OPERATIONS / DISPATCH
            </span>
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5">
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Live crowd density, sensor inflow/outflow, and train GPS tracking</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Simulate and report line signal and obstruction delays</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Acknowledge and resolve overcrowding and line warnings</span>
            </li>
            <li className="flex items-center space-x-2">
              <BadgeCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Execute manual headway adjustments based on AI guidance</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Staff Directory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Users className="w-4 h-4 text-blue-400" />
            <span>Active Operations Personnel Directory</span>
          </h3>
          <span className="text-xs text-slate-400">{users.length} Registered Accounts</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Badge ID</th>
                <th className="py-3 px-4">Personnel Name</th>
                <th className="py-3 px-4">Transit Email</th>
                <th className="py-3 px-4">Operational Title</th>
                <th className="py-3 px-4 text-center">Assigned Role</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">{u.badge_id}</td>
                  <td className="py-3 px-4 font-bold text-white">{u.name}</td>
                  <td className="py-3 px-4 text-slate-400">{u.email}</td>
                  <td className="py-3 px-4 text-slate-300">{u.title}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                      u.role === 'admin' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center space-x-1 text-emerald-400 font-semibold text-[11px]">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span>Authorized</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Operator Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-[2300] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl p-6 text-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <UserPlus className="w-5 h-5 text-purple-400" />
                <span>Create Staff Account</span>
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                &times;
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 bg-red-500/20 border border-red-500/40 rounded-xl text-xs text-red-300">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  placeholder="e.g. David Kim"
                  required
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Transit Email</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={e => setNewEmail(e.target.value)}
                  placeholder="e.g. dkim@metroflow.ny"
                  required
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Temporary password"
                  required
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Role</label>
                  <select
                    value={newRole}
                    onChange={e => setNewRole(e.target.value as any)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="operator">Operator</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Badge ID</label>
                  <input
                    type="text"
                    value={newBadge}
                    onChange={e => setNewBadge(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Job Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder="e.g. Lexington Line Dispatcher"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-purple-600/30 cursor-pointer"
                >
                  Confirm & Provision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
