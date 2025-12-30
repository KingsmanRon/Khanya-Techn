/**
 * Command Palette Component
 * Quick search and navigation (Cmd+K)
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  ScrollText,
  TrendingUp,
  Award,
  Scale,
  Blocks,
  Settings,
  Search,
  ArrowRight,
  Clock,
} from 'lucide-react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from './ui/command';

const navigationItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, keywords: ['home', 'overview'] },
  { name: 'Agents', href: '/agents', icon: Users, keywords: ['registry', 'mtp-id'] },
  { name: 'Register New Agent', href: '/agents/new', icon: Users, keywords: ['create', 'add'] },
  { name: 'Audit Trail', href: '/audit', icon: ScrollText, keywords: ['events', 'logs', 'history'] },
  { name: 'Trust Scores', href: '/trust', icon: TrendingUp, keywords: ['reputation', 'score'] },
  { name: 'Certifications', href: '/certifications', icon: Award, keywords: ['za-fin', 'popia', 'eu-ai'] },
  { name: 'Disputes', href: '/disputes', icon: Scale, keywords: ['resolve', 'arbitration'] },
  { name: 'Blockchain', href: '/blockchain', icon: Blocks, keywords: ['merkle', 'anchor', 'base-l2'] },
  { name: 'Settings', href: '/settings', icon: Settings, keywords: ['config', 'preferences'] },
];

const quickActions = [
  { name: 'Search Agent by MTP ID', action: 'search-agent', icon: Search },
  { name: 'View Recent Audit Events', action: 'recent-audits', icon: Clock },
];

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [recentSearches] = useState([
    'MTP-a3f5b2-7k9m2p',
    'First National Bank',
    'fraud_detection',
  ]);

  // Reset search when closed
  useEffect(() => {
    if (!open) {
      setSearch('');
    }
  }, [open]);

  const handleSelect = (href) => {
    onClose();
    navigate(href);
  };

  const handleAction = (action) => {
    onClose();
    switch (action) {
      case 'search-agent':
        navigate('/agents?search=true');
        break;
      case 'recent-audits':
        navigate('/audit?filter=recent');
        break;
      default:
        break;
    }
  };

  const filteredNavigation = useMemo(() => {
    if (!search) return navigationItems;
    const lowerSearch = search.toLowerCase();
    return navigationItems.filter(
      (item) =>
        item.name.toLowerCase().includes(lowerSearch) ||
        item.keywords.some((k) => k.includes(lowerSearch))
    );
  }, [search]);

  return (
    <CommandDialog open={open} onOpenChange={onClose}>
      <CommandInput
        placeholder="Search pages, agents, actions..."
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        {/* Quick Actions */}
        {!search && (
          <>
            <CommandGroup heading="Quick Actions">
              {quickActions.map((action) => (
                <CommandItem
                  key={action.action}
                  onSelect={() => handleAction(action.action)}
                  className="flex items-center gap-3 cursor-pointer"
                >
                  <action.icon className="h-4 w-4 text-slate-400" />
                  <span>{action.name}</span>
                  <ArrowRight className="ml-auto h-4 w-4 text-slate-500" />
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}

        {/* Recent Searches */}
        {!search && recentSearches.length > 0 && (
          <>
            <CommandGroup heading="Recent Searches">
              {recentSearches.map((term) => (
                <CommandItem
                  key={term}
                  onSelect={() => {
                    onClose();
                    navigate(`/agents?q=${encodeURIComponent(term)}`);
                  }}
                  className="flex items-center gap-3 cursor-pointer"
                >
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="font-mono text-sm">{term}</span>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}

        {/* Navigation */}
        <CommandGroup heading="Pages">
          {filteredNavigation.map((item) => (
            <CommandItem
              key={item.href}
              onSelect={() => handleSelect(item.href)}
              className="flex items-center gap-3 cursor-pointer"
            >
              <item.icon className="h-4 w-4 text-slate-400" />
              <span>{item.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
