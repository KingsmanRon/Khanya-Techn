/**
 * Sidebar Navigation Component
 * Main navigation for the MTP Dashboard
 */
import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  ScrollText,
  TrendingUp,
  Award,
  Scale,
  Blocks,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, permission: null },
  { name: 'Agents', href: '/agents', icon: Users, permission: 'view:agents' },
  { name: 'Audit Trail', href: '/audit', icon: ScrollText, permission: 'view:audit' },
  { name: 'Trust Scores', href: '/trust', icon: TrendingUp, permission: 'view:trust' },
  { name: 'Certifications', href: '/certifications', icon: Award, permission: 'view:certifications' },
  { name: 'Disputes', href: '/disputes', icon: Scale, permission: 'view:disputes' },
  { name: 'Blockchain', href: '/blockchain', icon: Blocks, permission: 'view:blockchain' },
];

const bottomNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings, permission: null },
];

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();
  const { hasPermission, user } = useAuth();

  const NavItem = ({ item }) => {
    // Check permission if required
    if (item.permission && !hasPermission(item.permission)) {
      return null;
    }

    const isActive = location.pathname === item.href ||
      (item.href !== '/' && location.pathname.startsWith(item.href));

    return (
      <NavLink
        to={item.href}
        className={cn(
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
          isActive
            ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/50',
          collapsed && 'justify-center px-2'
        )}
        title={collapsed ? item.name : undefined}
      >
        <item.icon className={cn('h-5 w-5 flex-shrink-0', isActive && 'text-white')} />
        {!collapsed && <span>{item.name}</span>}
      </NavLink>
    );
  };

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-slate-900 border-r border-slate-800 transition-all duration-300 flex flex-col',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className={cn(
        'flex items-center h-16 px-4 border-b border-slate-800',
        collapsed ? 'justify-center' : 'gap-3'
      )}>
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700">
          <Shield className="h-6 w-6 text-white" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-lg font-bold text-white">MTP</span>
            <span className="text-xs text-slate-500">Trust Protocol</span>
          </div>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="px-3 py-4 border-t border-slate-800 space-y-1">
        {bottomNavigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-20 flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>

      {/* User Info (when not collapsed) */}
      {!collapsed && user && (
        <div className="px-4 py-3 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white text-sm font-medium">
              {user.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name}</p>
              <p className="text-xs text-slate-500 truncate">{user.org}</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
