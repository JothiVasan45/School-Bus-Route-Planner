import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import {
  LayoutDashboard, Database, Route, Sliders, GitCompare,
  Users, BarChart3, WifiOff, FlaskConical, MessageSquare,
  FileText, Settings, Bus, LogOut, Menu, X, Zap
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard',    icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/data',         icon: Database,        label: 'Dataset' },
  { to: '/routes',       icon: Route,           label: 'Routes' },
  { to: '/optimization', icon: Sliders,         label: 'Optimizer' },
  { to: '/comparison',   icon: GitCompare,      label: 'Comparison' },
  { to: '/workload',     icon: Users,           label: 'Workload' },
  { to: '/reliability',  icon: BarChart3,       label: 'Reliability' },
  { to: '/fallback',     icon: WifiOff,         label: 'Fallback' },
  { to: '/experiments',  icon: FlaskConical,    label: 'Experiments' },
  { to: '/validation',   icon: MessageSquare,   label: 'Validation' },
  { to: '/reports',      icon: FileText,        label: 'Reports' },
  { to: '/settings',     icon: Settings,        label: 'Settings' },
]

export default function Layout() {
  const { username, role, fullName, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={clsx(
          'flex flex-col bg-card border-r border-border transition-all duration-300 ease-in-out',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-border">
          <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Bus className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="text-sm font-bold text-white truncate">BusRoute Pro</div>
              <div className="text-xs text-slate-400 truncate">Multi-Objective Planner</div>
            </div>
          )}
          <button
            className="ml-auto text-slate-400 hover:text-white p-1 rounded"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => {
            const active = location.pathname === to
            return (
              <NavLink
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium',
                  active
                    ? 'text-white bg-primary-600/20 border border-primary-600/40'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/60'
                )}
                title={collapsed ? label : ''}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {!collapsed && <span>{label}</span>}
              </NavLink>
            )
          })}
        </nav>

        {/* User info */}
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary-700 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
              {(fullName || username || 'U')[0].toUpperCase()}
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-white truncate">{fullName || username}</div>
                <div className="text-xs text-slate-400 capitalize">{role}</div>
              </div>
            )}
            <button
              onClick={logout}
              className="text-slate-400 hover:text-red-400 transition-colors p-1 rounded"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="min-h-full p-6 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
