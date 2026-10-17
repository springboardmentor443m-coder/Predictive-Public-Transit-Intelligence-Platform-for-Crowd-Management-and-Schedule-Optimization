import React, { useState, useEffect } from 'react';
import { User, UserRole } from '../types/auth';
import { userService } from '../services/userService';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Input } from '../components/common/Input';
import { Modal } from '../components/common/Modal';
import { useAuth } from '../hooks/useAuth';
import { UserPlus, Shield, UserCheck, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';

export const UserManagementPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [newEmail, setNewEmail] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [newRole, setNewRole] = useState<UserRole>('OPERATOR');
  const [createLoading, setCreateLoading] = useState<boolean>(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await userService.listUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);
    try {
      await userService.createUser({
        email: newEmail,
        name: newName,
        password: newPassword,
        role: newRole,
        is_active: true,
      });
      setSuccessMsg(`User ${newEmail} created successfully.`);
      setIsModalOpen(false);
      setNewEmail('');
      setNewName('');
      setNewPassword('');
      setNewRole('OPERATOR');
      await fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleRoleChange = async (targetUser: User, role: UserRole) => {
    try {
      await userService.updateUserRole(targetUser.id, role);
      setSuccessMsg(`Updated role for ${targetUser.email} to ${role}.`);
      await fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user role.');
    }
  };

  const handleStatusToggle = async (targetUser: User) => {
    try {
      await userService.updateUserStatus(targetUser.id, !targetUser.is_active);
      setSuccessMsg(
        `Account ${targetUser.email} is now ${!targetUser.is_active ? 'Active' : 'Deactivated'}.`
      );
      await fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-100 font-mono tracking-wide">
            USER MANAGEMENT PORTAL
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            System Administrator Control: Provision operator accounts, assign RBAC permissions, and manage access statuses.
          </p>
        </div>

        <Button variant="primary" onClick={() => setIsModalOpen(true)}>
          <UserPlus className="w-4 h-4 mr-1" />
          Provision New User
        </Button>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            {successMsg}
          </span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:underline">Dismiss</button>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </span>
          <button onClick={() => setError(null)} className="text-rose-400 hover:underline">Dismiss</button>
        </div>
      )}

      {/* User Table Card */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-mono uppercase tracking-wider text-slate-400">
                <th className="p-4">User Details</th>
                <th className="p-4">Assigned Role</th>
                <th className="p-4">Account Status</th>
                <th className="p-4">Created Date</th>
                <th className="p-4 text-right">RBAC Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 font-mono">
                    Loading system users...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 font-mono">
                    No system users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-4">
                      <div className="font-semibold text-slate-200">{u.name}</div>
                      <div className="text-xs font-mono text-slate-400">{u.email}</div>
                    </td>
                    <td className="p-4">
                      <Badge variant={u.role === 'ADMIN' ? 'purple' : 'cyan'}>
                        {u.role === 'ADMIN' ? <Shield className="w-3 h-3 inline mr-1" /> : <UserCheck className="w-3 h-3 inline mr-1" />}
                        {u.role}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <Badge variant={u.is_active ? 'emerald' : 'rose'}>
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </Badge>
                    </td>
                    <td className="p-4 text-xs font-mono text-slate-400">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* Role selection dropdown */}
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u, e.target.value as UserRole)}
                          disabled={u.id === currentUser?.id}
                          className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyan-500 disabled:opacity-40"
                        >
                          <option value="OPERATOR">OPERATOR</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>

                        {/* Status toggle button */}
                        <Button
                          variant={u.is_active ? 'ghost' : 'outline'}
                          size="sm"
                          onClick={() => handleStatusToggle(u)}
                          disabled={u.id === currentUser?.id}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Provision User Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="PROVISION NEW METROFLOW USER"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <Input
            label="Full Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="e.g. Alex Rivera"
            required
          />

          <Input
            label="Email Address"
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            placeholder="operator@metroflow.io"
            required
          />

          <Input
            label="Initial Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Minimum 8 characters"
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 tracking-wide uppercase font-mono">
              Role Permission Level
            </label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as UserRole)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="OPERATOR">OPERATOR (Operational Dashboard & Controls)</option>
              <option value="ADMIN">ADMIN (Full User & System Configuration Control)</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createLoading}>
              Provision User
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
