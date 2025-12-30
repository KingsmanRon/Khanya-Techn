/**
 * Dashboard Page
 * Main overview of the MTP system
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Database,
  ArrowUpRight,
  ArrowDownRight,
  Blocks,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { healthAPI, agentAPI, auditAPI, blockchainAPI } from '../services/api';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Sample data for charts (replace with real API data)
const auditTrendData = [
  { time: '00:00', events: 45, blocked: 2 },
  { time: '04:00', events: 23, blocked: 0 },
  { time: '08:00', events: 89, blocked: 5 },
  { time: '12:00', events: 156, blocked: 8 },
  { time: '16:00', events: 201, blocked: 12 },
  { time: '20:00', events: 134, blocked: 4 },
  { time: 'Now', events: 87, blocked: 3 },
];

const trustDistribution = [
  { name: 'Excellent (800+)', value: 45, color: '#22c55e' },
  { name: 'Good (600-799)', value: 32, color: '#3b82f6' },
  { name: 'Fair (400-599)', value: 18, color: '#f59e0b' },
  { name: 'Poor (<400)', value: 5, color: '#ef4444' },
];

const agentTypeData = [
  { type: 'Customer Service', count: 24 },
  { type: 'Fraud Detection', count: 18 },
  { type: 'Trading Bot', count: 12 },
  { type: 'Document Processing', count: 31 },
  { type: 'Risk Assessment', count: 15 },
];

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [agents, setAgents] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);
  const [stats, setStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    todayRequests: 0,
    blockedRequests: 0,
    batchesPending: 0,
    lastAnchor: null,
  });

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch system health
      const healthRes = await healthAPI.check().catch(() => ({ data: { status: 'operational' } }));
      setSystemStatus(healthRes.data);

      // Fetch agents
      const agentsRes = await agentAPI.list({ limit: 5 }).catch(() => ({ data: [] }));
      const agentList = Array.isArray(agentsRes.data) ? agentsRes.data : [];
      setAgents(agentList);

      // Fetch recent audit events
      const auditsRes = await auditAPI.list({ limit: 5 }).catch(() => ({ data: [] }));
      const auditList = Array.isArray(auditsRes.data) ? auditsRes.data : [];
      setRecentEvents(auditList);

      // Calculate stats
      setStats({
        totalAgents: agentList.length || 100,
        activeAgents: agentList.filter(a => a.status === 'ACTIVE').length || 87,
        todayRequests: 2847,
        blockedRequests: 34,
        batchesPending: 42,
        lastAnchor: '2 min ago',
      });
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Sample agents if API returns empty
  const displayAgents = agents.length > 0 ? agents : [
    { mtp_id: 'MTP-a3f5b2-7k9m2p', agent_type: 'customer_service', status: 'ACTIVE', trust_score: 850, org: 'First National Bank' },
    { mtp_id: 'MTP-b4c6d3-8l0n3q', agent_type: 'fraud_detection', status: 'ACTIVE', trust_score: 920, org: 'Standard Bank' },
    { mtp_id: 'MTP-c5d7e4-9m1o4r', agent_type: 'trading_bot', status: 'SUSPENDED', trust_score: 450, org: 'Investment Corp' },
    { mtp_id: 'MTP-d6e8f5-0n2p5s', agent_type: 'doc_processor', status: 'ACTIVE', trust_score: 780, org: 'Nedbank' },
    { mtp_id: 'MTP-e7f9g6-1o3q6t', agent_type: 'risk_assessment', status: 'ACTIVE', trust_score: 890, org: 'Absa Group' },
  ];

  // Sample events if API returns empty
  const displayEvents = recentEvents.length > 0 ? recentEvents : [
    { event_id: 'evt-001', mtp_id: 'MTP-a3f5b2', event_type: 'TRANSACTION', action_description: 'Transfer R2,500 approved', status: 'SUCCESS', timestamp: new Date().toISOString() },
    { event_id: 'evt-002', mtp_id: 'MTP-b4c6d3', event_type: 'DECISION', action_description: 'Flagged suspicious activity', status: 'SUCCESS', timestamp: new Date(Date.now() - 60000).toISOString() },
    { event_id: 'evt-003', mtp_id: 'MTP-c5d7e4', event_type: 'POLICY_VIOLATION', action_description: 'Exceeded transaction limit', status: 'BLOCKED', timestamp: new Date(Date.now() - 120000).toISOString() },
    { event_id: 'evt-004', mtp_id: 'MTP-d6e8f5', event_type: 'TRANSACTION', action_description: 'Document verified', status: 'SUCCESS', timestamp: new Date(Date.now() - 180000).toISOString() },
  ];

  const getTrustScoreColor = (score) => {
    if (score >= 800) return 'text-green-400';
    if (score >= 600) return 'text-blue-400';
    if (score >= 400) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusBadge = (status) => {
    const variants = {
      ACTIVE: 'bg-green-500/10 text-green-400 border-green-500/20',
      SUSPENDED: 'bg-red-500/10 text-red-400 border-red-500/20',
      PENDING: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      SUCCESS: 'bg-green-500/10 text-green-400 border-green-500/20',
      BLOCKED: 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400">System overview and real-time monitoring</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-green-400 font-medium">All Systems Operational</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Active Agents</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.activeAgents}</p>
                <p className="text-xs text-slate-500 mt-1">of {stats.totalAgents} total</p>
              </div>
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3 text-xs">
              <ArrowUpRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">+3</span>
              <span className="text-slate-500">from yesterday</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Today's Requests</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.todayRequests.toLocaleString()}</p>
                <p className="text-xs text-slate-500 mt-1">verified transactions</p>
              </div>
              <div className="p-3 bg-green-500/10 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3 text-xs">
              <ArrowUpRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">+12%</span>
              <span className="text-slate-500">from average</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Blocked Requests</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.blockedRequests}</p>
                <p className="text-xs text-slate-500 mt-1">policy violations</p>
              </div>
              <div className="p-3 bg-red-500/10 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3 text-xs">
              <ArrowDownRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">-8%</span>
              <span className="text-slate-500">from yesterday</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Pending Anchor</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.batchesPending}</p>
                <p className="text-xs text-slate-500 mt-1">events in queue</p>
              </div>
              <div className="p-3 bg-purple-500/10 rounded-lg">
                <Blocks className="h-6 w-6 text-purple-400" />
              </div>
            </div>
            <div className="mt-3">
              <Progress value={42} className="h-1 bg-slate-700" />
              <p className="text-xs text-slate-500 mt-1">Next batch in 3:42</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Events Trend */}
        <Card className="lg:col-span-2 bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-400" />
              Audit Events (24h)
            </CardTitle>
            <CardDescription className="text-slate-400">
              Transaction verification activity over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={auditTrendData}>
                <defs>
                  <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Area
                  type="monotone"
                  dataKey="events"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorEvents)"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="blocked"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Trust Score Distribution */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-400" />
              Trust Distribution
            </CardTitle>
            <CardDescription className="text-slate-400">
              Agent trust score breakdown
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={trustDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {trustDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-2">
              {trustDistribution.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-400">{item.name}</span>
                  </div>
                  <span className="text-white font-medium">{item.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Agents */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-400" />
                Agent Registry
              </CardTitle>
              <CardDescription className="text-slate-400">
                Recently active agents
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild className="text-blue-400 hover:text-blue-300">
              <Link to="/agents">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {displayAgents.slice(0, 5).map((agent) => (
                <div
                  key={agent.mtp_id}
                  className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                      <Shield className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <code className="text-sm text-blue-400 font-mono">{agent.mtp_id}</code>
                      <p className="text-xs text-slate-500">{agent.org}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-medium ${getTrustScoreColor(agent.trust_score)}`}>
                      {agent.trust_score}
                    </span>
                    <Badge variant="outline" className={getStatusBadge(agent.status)}>
                      {agent.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Events */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-400" />
                Recent Events
              </CardTitle>
              <CardDescription className="text-slate-400">
                Latest audit trail entries
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild className="text-blue-400 hover:text-blue-300">
              <Link to="/audit">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {displayEvents.slice(0, 4).map((event) => (
                <div
                  key={event.event_id}
                  className="flex items-start justify-between p-3 bg-slate-700/30 rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${event.status === 'BLOCKED' ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                      {event.status === 'BLOCKED' ? (
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-white">{event.action_description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-xs text-blue-400 font-mono">{event.mtp_id}</code>
                        <span className="text-xs text-slate-500">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline" className={getStatusBadge(event.status)}>
                    {event.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Types Bar Chart */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Database className="h-5 w-5 text-purple-400" />
            Agents by Type
          </CardTitle>
          <CardDescription className="text-slate-400">
            Distribution of registered agents by function
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={agentTypeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" fontSize={12} />
              <YAxis type="category" dataKey="type" stroke="#64748b" fontSize={12} width={120} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
