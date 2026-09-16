import { useCallback, useEffect, useState } from "react";
import { Cpu, Database, Loader2, ShieldCheck, UserCog, KeyRound } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { useAuth, withAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";

function Settings() {
  const { user, hasRole, refreshUser } = useAuth();
  const { showToast } = useToast();
  const isAdmin = hasRole("admin");

  const [profileForm, setProfileForm] = useState({ full_name: "", password: "" });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState("");

  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({ email: "", full_name: "", role: "operator", password: "" });
  const [creatingUser, setCreatingUser] = useState(false);

  useEffect(() => {
    if (user) setProfileForm({ full_name: user.full_name, password: "" });
  }, [user]);

  const loadUsers = useCallback(() => {
    if (!isAdmin) return;
    api.get("/users").then((r) => setUsers(r.data)).catch(() => {});
  }, [isAdmin]);

  useEffect(loadUsers, [loadUsers]);

  async function saveProfile(e) {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg("");
    try {
      const payload = { full_name: profileForm.full_name };
      if (profileForm.password) payload.password = profileForm.password;
      await api.put("/users/me", payload);
      await refreshUser();
      setProfileMsg("Profile updated successfully.");
      showToast("Profile settings saved", "success");
      setProfileForm((f) => ({ ...f, password: "" }));
    } catch (err) {
      const msg = err?.response?.data?.detail ? `Update failed: ${err.response.data.detail}` : "Update failed.";
      setProfileMsg(msg);
      showToast(msg, "error");
    } finally {
      setSavingProfile(false);
    }
  }

  async function createUser(e) {
    e.preventDefault();
    setCreatingUser(true);
    try {
      await api.post("/users", newUser);
      showToast(`Created account for ${newUser.full_name}`, "success");
      setNewUser({ email: "", full_name: "", role: "operator", password: "" });
      loadUsers();
    } catch (err) {
      showToast(err?.response?.data?.detail || "Failed to create user", "error");
    } finally {
      setCreatingUser(false);
    }
  }

  async function toggleActive(u) {
    try {
      await api.post(`/users/${u.id}/deactivate`);
      showToast(`Toggled activation status for ${u.full_name}`, "info");
      loadUsers();
    } catch (err) {
      showToast("Could not update user status", "error");
    }
  }

  return (
    <DashboardLayout title="Settings & User Administration" subtitle="Account preferences · security · role-based access control (RBAC)">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Profile Settings Card */}
        <div className="card card-pad border-slate-800 self-start space-y-5">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-indigo-600 text-lg font-extrabold text-white shadow-lg shadow-brand-500/20">
              {user?.full_name?.split(" ").map((w) => w[0]).slice(0, 2).join("")}
            </span>
            <div>
              <p className="font-extrabold text-white text-base">{user?.full_name}</p>
              <p className="text-xs text-slate-400 capitalize">{user?.role} · {user?.email}</p>
            </div>
          </div>

          <form onSubmit={saveProfile} className="space-y-4 border-t border-slate-800/80 pt-4">
            <div>
              <label className="label">Full Name</label>
              <input
                className="input"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
              />
            </div>

            <div>
              <label className="label">New Password (optional)</label>
              <div className="relative">
                <input
                  type="password"
                  className="input font-mono"
                  placeholder="Leave blank to keep current password"
                  value={profileForm.password}
                  onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })}
                />
              </div>
            </div>

            <button type="submit" disabled={savingProfile} className="btn-primary w-full py-2.5 text-xs font-extrabold">
              {savingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Save Account Changes
            </button>

            {profileMsg && (
              <p className="text-center text-xs font-bold text-emerald-400">{profileMsg}</p>
            )}
          </form>

          <div className="rounded-xl bg-slate-950 p-4 border border-slate-800 space-y-2">
            <p className="flex items-center gap-1.5 text-xs font-extrabold text-white">
              <ShieldCheck className="h-4 w-4 text-emerald-400" /> RBAC Role Matrix
            </p>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>· <span className="font-bold text-white">Admin:</span> Full control, emergency broadcasts, user management</li>
              <li>· <span className="font-bold text-white">Operator:</span> Timetable edits, delay reports, sensor ingest</li>
              <li>· <span className="font-bold text-white">Viewer:</span> Read-only monitoring, predictions & analytics</li>
            </ul>
          </div>
        </div>

        {/* User Management Administration Card */}
        <div className="card xl:col-span-2 border-slate-800">
          <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/15 border border-brand-500/30 text-brand-400">
              <UserCog className="h-4 w-4" />
            </span>
            <h3 className="font-extrabold tracking-tight text-white">User Administration & Accounts</h3>
            <span className="ml-auto text-xs font-mono text-slate-400">{users.length} registered accounts</span>
          </div>

          {!isAdmin ? (
            <p className="px-5 py-16 text-center text-sm text-slate-500">
              Administrator privileges required to manage accounts. Contact your system admin for support.
            </p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Account Status</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-850/60 transition">
                        <td className="font-extrabold text-white">{u.full_name}</td>
                        <td className="font-mono text-xs text-slate-300">{u.email}</td>
                        <td>
                          <StatusBadge value={u.role} />
                        </td>
                        <td>
                          {u.is_active ? (
                            <span className="font-bold text-emerald-400 text-xs flex items-center gap-1">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Active
                            </span>
                          ) : (
                            <span className="font-bold text-slate-500 text-xs">Deactivated</span>
                          )}
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => toggleActive(u)}
                            disabled={u.id === user?.id}
                            className="rounded-lg px-2.5 py-1 text-xs font-bold text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-30"
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add New User Form */}
              <form
                onSubmit={createUser}
                className="grid grid-cols-1 gap-3 border-t border-slate-800 bg-slate-950/60 p-5 sm:grid-cols-5"
              >
                <input
                  required
                  type="email"
                  placeholder="Operator Email"
                  className="input"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
                <input
                  required
                  placeholder="Full Name"
                  className="input"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                />
                <select
                  className="input"
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                >
                  <option value="operator">Operator</option>
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                </select>
                <input
                  required
                  type="password"
                  minLength={8}
                  placeholder="Password (8+ chars)"
                  className="input font-mono"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                />
                <button type="submit" disabled={creatingUser} className="btn-primary py-2.5 text-xs font-extrabold">
                  {creatingUser ? <Loader2 className="h-4 w-4 animate-spin" /> : "Add User Account"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>

      {/* System Infrastructure Telemetry Card */}
      <div className="mt-5 card card-pad border-slate-800">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-3 mb-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
            <Cpu className="h-5 w-5" />
          </span>
          <div>
            <h3 className="font-extrabold tracking-tight text-white">System Infrastructure & Dependency Telemetry</h3>
            <p className="text-xs text-slate-400">Fault tolerant services and DB session health</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["FastAPI Backend", "Running :8000", "Python 3.11", true],
            ["PostgreSQL Relational DB", "Active Session", "Core Storage", true],
            ["Socket.IO Realtime", "Broadcast Loop", "WebSocket / WSS", true],
            ["Redis & Mongo Cache", "Operational", "In-Memory Fallback", true],
          ].map(([name, status, tech, ok]) => (
            <div key={name} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-extrabold text-white">{name}</p>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <p className="mt-1 text-sm font-extrabold font-mono text-emerald-400">{status}</p>
              <p className="mt-0.5 text-[10px] text-slate-500">{tech}</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Settings);
