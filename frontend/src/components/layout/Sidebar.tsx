import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  Radio, 
  Map as MapIcon, 
  TrendingUp, 
  Clock, 
  Users, 
  ShieldAlert,
  BarChart2,
  FileText,
  Activity,
  AlertTriangle,
  Server,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();

  const navigation: NavSection[] = [
    {
      title: 'CORE OPERATIONS',
      items: [
        { name: 'System Overview', href: '/overview', icon: Activity },
        { name: 'Live Monitoring', href: '/live-monitoring', icon: Radio },
      ],
    },
    {
      title: 'INSIGHTS',
      items: [
        { name: 'Crowd Intelligence', href: '/dashboard', icon: Users },
        { name: 'Network Analysis', href: '/network', icon: MapIcon },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Alerts', href: '/alerts', icon: ShieldAlert },
        { name: 'Analytics', href: '/analytics', icon: BarChart2 },
      ],
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { name: 'User Management', href: '/admin/users', icon: Users, adminOnly: true },
        { name: 'Audit Logs', href: '/admin/audit-logs', icon: FileText, adminOnly: true },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-[#E8E4D8] border-r border-[#DDD9CF] flex flex-col h-full sticky top-0">
      <div className="h-16 flex items-center px-6 border-b border-[#DDD9CF]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#2F6F68] flex items-center justify-center text-white">
            <Radio className="w-5 h-5" />
          </div>
          <span className="text-xl font-bold text-[#29322F] tracking-wide">MetroFlow</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
        {navigation.map((section) => {
          const visibleItems = section.items.filter(item => !item.adminOnly || user?.role === 'ADMIN');
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title}>
              <div className="px-3 mb-2 text-xs font-semibold text-[#6F8F87] uppercase tracking-wider">
                {section.title}
              </div>
              <nav className="space-y-1">
                {visibleItems.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={`
                        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200
                        ${isActive 
                          ? 'bg-white text-[#29322F] font-semibold border border-[#DDD9CF] shadow-sm' 
                          : 'text-[#6F8F87] hover:bg-[#DDD9CF] hover:text-[#29322F] font-medium'
                        }
                      `}
                    >
                      <item.icon className={`w-5 h-5 ${isActive ? 'text-[#2F6F68]' : 'opacity-70'}`} />
                      {item.name}
                    </NavLink>
                  );
                })}
              </nav>
            </div>
          );
        })}
      </div>

      <div className="p-4 border-t border-[#DDD9CF]">
        <div className="p-3 rounded-xl bg-white border border-[#DDD9CF] flex items-center gap-3 shadow-sm">
          <div className="w-2 h-2 rounded-full bg-[#4F8A63] animate-pulse" />
          <div className="text-xs">
            <div className="text-[#29322F] font-semibold">Live Data Sync</div>
            <div className="text-[#6F8F87]">GTFS-RT Connected</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
