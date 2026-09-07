import { useCallback, useEffect, useState } from "react";
import { Loader2, ShieldCheck, UserCog } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { useAuth, withAuth } from "../../lib/auth";
import api from "../../lib/api";

function Settings() {
  const { user, hasRole, refreshUser } = useAuth();
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
      setProfileMsg("Profile updated.");
      setProfileForm((f) => ({ ...f, password: "" }));
    } catch (err) {
      setProfileMsg(
        err?.response?.data?.detail
          ? `Update failed: ${err.response.data.detail}`
          : "Update failed."
      );
    } finally {
      setSavingProfile(false);
    }
  }

  async function createUser(e) {
    e.preventDefault();
    setCreatingUser(true);
    try {
      await api.post("/users", newUser);
      setNewUser({ email: "", full_name: "", role: "operator", password: "" });
      loadUsers();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to create user");
    } finally {
      setCreatingUser(false);
    }
  }

  async function toggleActive(u) {
    try {
      await api.post(`/users/${u.id}/deactivate`);
      loadUsers();
    } catch {}
  }

  return (
    <DashboardLayout title="Settings & Profile" subtitle="Account preferences · user administration">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Profile */}
        <div className="card card-pad self-start">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-100 text-base font-bold text-brand-700">
              {user?.full_name?.split(" ").map((w) => w[0]).slice(0, 2).join("")}
            </span>
            <div>
              <p className="font-semibold text-slate-900">{user?.full_name}</p>
              <p className="text-xs capitalize text-slate-500">{user?.role} · {user?.email}</p>
            </div>
          </div>

          <form onSubmit={saveProfile} className="mt-5 space-y-4 border-t border-slate-200 pt-5">
            <div>
              <label className="label">Full name</label>
              <input
                className="input"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="label">New password (optional)</label>
              <input
                type="password"
                className="input"
                placeholder="Leave blank to keep current"
                value={profileForm.password}
                onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })}
              />
            </div>
            <button type="submit" disabled={savingProfile} className="btn-primary w-full">
              {savingProfile && <Loader2 className="h-4 w-4 animate-spin" />}
              Save changes
            </button>
            {profileMsg && <p className="text-center text-xs font-medium text-emerald-600">{profileMsg}</p>}
          </form>

          <div className="mt-6 rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
              <ShieldCheck className="h-4 w-4 text-emerald-500" /> Role permissions
            </p>
            <ul className="mt-2 space-y-1 text-xs text-slate-500">
              <li>· Admin — full control, broadcasts, user management</li>
              <li>· Operator — schedules, delays, acknowledge alerts</li>
              <li>· Viewer — read-only monitoring & analytics</li>
            </ul>
          </div>
        </div>

        {/* Users admin */}
        <div className="card xl:col-span-2">
          <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <UserCog className="h-4 w-4" />
            </span>
            <h3 className="font-semibold text-slate-900">User Management</h3>
            <span className="ml-auto text-xs text-slate-400">{users.length} accounts</span>
          </div>

          {!isAdmin ? (
            <p className="px-5 py-10 text-center text-sm text-slate-400">
              Administrator access required to manage users.
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
                      <th>Status</th>
                      <th className="text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td className="font-semibold text-slate-800">{u.full_name}</td>
                        <td>{u.email}</td>
                        <td>
                          <StatusBadge value={u.role === "admin" ? "critical" : u.role === "operator" ? "medium" : "low"} />
                          <span className="ml-1.5 text-xs capitalize text-slate-500">{u.role}</span>
                        </td>
                        <td>
                          {u.is_active ? (
                            <span className="font-semibold text-emerald-600">Active</span>
                          ) : (
                            <span className="font-semibold text-slate-400">Disabled</span>
                          )}
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => toggleActive(u)}
                            disabled={u.id === user?.id}
                            className="rounded-md px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-slate-100 disabled:opacity-40"
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <form onSubmit={createUser} className="grid grid-cols-1 gap-3 border-t border-slate-200 bg-slate-50/60 p-5 sm:grid-cols-5">
                <input
                  required
                  type="email"
                  placeholder="Email"
                  className="input"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
                <input
                  required
                  placeholder="Full name"
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
                  placeholder="Password (8+)"
                  className="input"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                />
                <button type="submit" disabled={creatingUser} className="btn-primary">
                  {creatingUser && <Loader2 className="h-4 w-4 animate-spin" />}
                  Add user
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Settings);
