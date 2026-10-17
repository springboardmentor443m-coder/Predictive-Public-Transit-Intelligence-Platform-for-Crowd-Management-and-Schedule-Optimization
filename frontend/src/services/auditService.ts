import { api } from './api';
import { AuditLog } from '../types/audit';

export const auditService = {
  async getAuditLogs(action?: string, actorEmail?: string): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (actorEmail) params.append('actor_email', actorEmail);

    const response = await api.get<AuditLog[]>('/audit-logs', { params });
    return response.data;
  },
};
