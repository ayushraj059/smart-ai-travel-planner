import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  MapPin,
  User,
  Sun,
  Moon,
  Monitor,
  LogOut,
  Compass,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
  { icon: MapPin, label: 'My Trips', to: '/trips' },
  { icon: User, label: 'Profile', to: '/profile' },
];

const themeOptions: { key: Theme; icon: typeof Sun; label: string }[] = [
  { key: 'light', icon: Sun, label: 'Light' },
  { key: 'dark', icon: Moon, label: 'Dark' },
  { key: 'system', icon: Monitor, label: 'System' },
];

export default function Sidebar() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<Theme>('system');

  return (
    <div className="w-52 min-h-screen bg-navy-800 border-r border-navy-400 flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-navy-400">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-indigo-600 rounded-md flex items-center justify-center">
            <Compass size={15} className="text-white" />
          </div>
          <span className="text-white font-semibold text-base tracking-tight">Voyonata</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2.5 pt-4 space-y-0.5">
        {navItems.map(({ icon: Icon, label, to }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-300 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-navy-500'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={15} className={isActive ? 'text-indigo-400' : 'text-slate-500'} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-2.5 pb-4 space-y-2 border-t border-navy-400 pt-3">
        {user && (
          <div className="flex items-center gap-2.5 px-3 py-2 mb-1">
            <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0">
              <span className="text-indigo-300 text-xs font-bold">
                {user.name[0].toUpperCase()}
              </span>
            </div>
            <p className="text-slate-300 text-xs font-medium truncate">{user.name}</p>
          </div>
        )}
        <button
          onClick={() => { logout(); navigate('/login'); }}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-navy-500 w-full transition-all"
        >
          <LogOut size={15} className="text-slate-500" />
          Sign Out
        </button>

        {/* Theme toggle */}
        <div className="flex items-center gap-0.5 bg-navy-500 rounded-lg p-1">
          {themeOptions.map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              onClick={() => setTheme(key)}
              title={label}
              className={`flex-1 flex items-center justify-center gap-1 py-1.5 rounded-md text-xs font-medium transition-all ${
                theme === key
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Icon size={11} />
              <span className="hidden xl:inline">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
