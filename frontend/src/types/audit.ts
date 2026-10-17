export interface AuditLog {
  id: number;
  actor_id: number | null;
  actor_email: string | null;
  action: string;
  ip_address: string | null;
  metadata_json: Record<string, any> | null;
  created_at: string;
}
