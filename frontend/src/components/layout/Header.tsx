import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../contexts/ThemeContext';
import { Badge } from '../common/Badge';
import { User, LogOut, Shield, UserCheck, Sun, Moon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-[#DDD9CF] bg-[#F7F5EF]/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Left side — logo / branding placeholder kept for layout balance */}
      <div />

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3 pl-4 border-l border-[#DDD9CF]">
            <div className="text-right">
              <div className="text-sm font-semibold text-[#29322F]">{user.name}</div>
              <div className="text-xs text-[#6F8F87] flex items-center justify-end gap-1 font-sans">
                <span>{user.email}</span>
              </div>
            </div>

            <Badge variant="cyan">
              {user.role === 'ADMIN' ? <Shield className="w-3 h-3 inline mr-1" /> : <UserCheck className="w-3 h-3 inline mr-1" />}
              {user.role}
            </Badge>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-white hover:bg-[#E8E4D8] text-[#29322F] hover:text-[#2F6F68] transition-colors border border-[#DDD9CF] shadow-sm flex items-center justify-center"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-[#2F6F68]" />
              )}
            </button>

            <button
              onClick={() => navigate('/profile')}
              className="p-2 rounded-lg bg-white hover:bg-[#E8E4D8] text-[#29322F] hover:text-[#2F6F68] transition-colors border border-[#DDD9CF]"
              title="View Profile"
            >
              <User className="w-4 h-4" />
            </button>

            <button
              onClick={handleLogout}
              className="p-2 rounded-lg bg-white hover:bg-[#B9574B]/10 text-[#29322F] hover:text-[#B9574B] transition-colors border border-[#DDD9CF]"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
