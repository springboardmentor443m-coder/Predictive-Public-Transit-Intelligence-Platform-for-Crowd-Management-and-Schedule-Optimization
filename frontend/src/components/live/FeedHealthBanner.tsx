import React from 'react';
import { FeedHealthSummary } from '../../services/liveService';
import { Badge } from '../common/Badge';
import { Radio, Clock, Zap, AlertTriangle, ShieldCheck } from 'lucide-react';

interface FeedHealthBannerProps {
  health: FeedHealthSummary | null;
  onRefresh: () => void;
  isSyncing: boolean;
}

export const FeedHealthBanner: React.FC<FeedHealthBannerProps> = ({
  health,
  onRefresh,
  isSyncing,
}) => {
  const getStatusBadgeVariant = (status?: string) => {
    switch (status) {
      case 'LIVE':
        return 'emerald';
      case 'CONNECTING':
        return 'amber';
      case 'STALE':
        return 'amber';
      case 'ERROR':
      case 'OFFLINE':
        return 'rose';
      default:
        return 'cyan';
    }
  };

  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400">
          <Radio className={`w-5 h-5 ${health?.is_live ? 'animate-pulse text-cyan-400' : 'text-amber-500'}`} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Live Transit Data Stream</span>
            <Badge variant={health?.is_live ? "cyan" : "amber"} size="sm">{health?.is_live ? "LIVE FEED" : "STALE FEED"}</Badge>
          </div>
          <h2 className="text-base font-bold text-slate-100 font-mono">
            {health?.provider_name || 'Official NYC MTA Subway GTFS-Realtime'}
          </h2>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-slate-500">Status:</span>
          <Badge variant={getStatusBadgeVariant(health?.status)}>
            {health?.status === 'LIVE' && <ShieldCheck className="w-3 h-3 inline mr-1" />}
            {(health?.status === 'STALE' || health?.status === 'UNAVAILABLE' || health?.status === 'ERROR') && <AlertTriangle className="w-3 h-3 inline mr-1" />}
            {health?.status || 'UNAVAILABLE'}
          </Badge>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-500">Latency:</span>
          <span className={health?.latency_ms != null ? "text-cyan-400 font-semibold" : "text-amber-500 font-semibold"}>
            {health?.latency_ms != null ? `${health.latency_ms} ms` : 'Unavailable'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-500">Last Update:</span>
          <span className="text-slate-200">
            {health?.received_at ? new Date(health.received_at).toLocaleTimeString() : 'Unavailable'}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isSyncing}
          className="px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-400 border border-cyan-800/60 transition-colors font-medium text-xs flex items-center gap-1.5 disabled:opacity-50"
        >
          <Radio className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          {isSyncing ? 'Syncing...' : 'Sync Feed'}
        </button>
      </div>
    </div>
  );
};
