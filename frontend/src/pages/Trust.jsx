/**
 * Trust Score Analytics Page
 * Visualize and analyze trust scores across agents
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Users,
  AlertTriangle,
  Award,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
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
  Legend,
} from 'recharts';
import { trustAPI, agentAPI } from '../services/api';

// Sample data
const TRUST_TREND_DATA = [
  { month: 'Jan', avg_score: 720, agents: 85 },
  { month: 'Feb', avg_score: 735, agents: 88 },
  { month: 'Mar', avg_score: 750, agents: 92 },
  { month: 'Apr', avg_score: 745, agents: 95 },
  { month: 'May', avg_score: 760, agents: 98 },
  { month: 'Jun', avg_score: 775, agents: 100 },
];

const DISTRIBUTION_DATA = [
  { name: 'Excellent (800+)', value: 45, color: '#22c55e' },
  { name: 'Good (600-799)', value: 32, color: '#3b82f6' },
  { name: 'Fair (400-599)', value: 18, color: '#f59e0b' },
  { name: 'Poor (<400)', value: 5, color: '#ef4444' },
];

const COMPONENT_SCORES = [
  { component: 'Reliability', avg: 82, description: 'Uptime and response consistency' },
  { component: 'Compliance', avg: 88, description: 'Policy adherence rate' },
  { component: 'Transparency', avg: 75, description: 'Audit trail completeness' },
  { component: 'History', avg: 85, description: 'Historical performance' },
];

const AT_RISK_AGENTS = [
  { mtp_id: 'MTP-c5d7e4-9m1o4r', org: 'Investment Corp', score: 450, change: -12, reason: 'Multiple policy violations' },
  { mtp_id: 'MTP-j2k4l1-6t8v1y', org: 'TymeBank', score: 380, change: -8, reason: 'Transaction limit exceeded' },
  { mtp_id: 'MTP-x3y5z6-7a8b9c', org: 'Alpha Trading', score: 420, change: -5, reason: 'Suspicious activity flags' },
];

const TOP_PERFORMERS = [
  { mtp_id: 'MTP-b4c6d3-8l0n3q', org: 'Standard Bank', score: 920, change: +5, type: 'fraud_detection' },
  { mtp_id: 'MTP-e7f9g6-1o3q6t', org: 'Absa Group', score: 890, change: +3, type: 'risk_assessment' },
  { mtp_id: 'MTP-a3f5b2-7k9m2p', org: 'First National Bank', score: 850, change: +2, type: 'customer_service' },
];

export default function Trust() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('6m');
  const [stats, setStats] = useState({
    avgScore: 775,
    totalAgents: 100,
    atRiskCount: 5,
    improvedCount: 72,
  });

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  const getTrustScoreColor = (score) => {
    if (score >= 800) return 'text-green-400';
    if (score >= 600) return 'text-blue-400';
    if (score >= 400) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreGradient = (score) => {
    if (score >= 800) return 'from-green-500 to-green-600';
    if (score >= 600) return 'from-blue-500 to-blue-600';
    if (score >= 400) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trust Score Analytics</h1>
          <p className="text-slate-400">Monitor and analyze trust scores across all agents</p>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[140px] bg-slate-800/50 border-slate-700 text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="3m">Last 3 months</SelectItem>
            <SelectItem value="6m">Last 6 months</SelectItem>
            <SelectItem value="1y">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Average Trust Score</p>
                <p className={`text-3xl font-bold mt-1 ${getTrustScoreColor(stats.avgScore)}`}>
                  {stats.avgScore}
                </p>
              </div>
              <div className={`p-3 rounded-lg bg-gradient-to-br ${getScoreGradient(stats.avgScore)}`}>
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs">
              <ArrowUpRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">+15</span>
              <span className="text-slate-500">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total Agents</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.totalAgents}</p>
              </div>
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs">
              <ArrowUpRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">+5</span>
              <span className="text-slate-500">new this month</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">At Risk</p>
                <p className="text-3xl font-bold text-red-400 mt-1">{stats.atRiskCount}</p>
              </div>
              <div className="p-3 bg-red-500/10 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs">
              <ArrowDownRight className="h-3 w-3 text-green-400" />
              <span className="text-green-400">-2</span>
              <span className="text-slate-500">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Improved</p>
                <p className="text-3xl font-bold text-green-400 mt-1">{stats.improvedCount}</p>
              </div>
              <div className="p-3 bg-green-500/10 rounded-lg">
                <Award className="h-6 w-6 text-green-400" />
              </div>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              72% of agents improved
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trust Score Trend */}
        <Card className="lg:col-span-2 bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Trust Score Trend</CardTitle>
            <CardDescription className="text-slate-400">Average trust score over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={TRUST_TREND_DATA}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} domain={[600, 900]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="avg_score"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribution */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Score Distribution</CardTitle>
            <CardDescription className="text-slate-400">Agents by trust tier</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={DISTRIBUTION_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {DISTRIBUTION_DATA.map((entry, index) => (
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
            <div className="space-y-2">
              {DISTRIBUTION_DATA.map((item) => (
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

      {/* Component Scores */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Score Components</CardTitle>
          <CardDescription className="text-slate-400">Average scores by trust component</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {COMPONENT_SCORES.map((comp) => (
              <div key={comp.component} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-white font-medium">{comp.component}</span>
                  <span className={`text-lg font-bold ${getTrustScoreColor(comp.avg * 10)}`}>
                    {comp.avg}%
                  </span>
                </div>
                <Progress value={comp.avg} className="h-2" />
                <p className="text-xs text-slate-500">{comp.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* At Risk Agents */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              Agents at Risk
            </CardTitle>
            <CardDescription className="text-slate-400">Agents with declining trust scores</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {AT_RISK_AGENTS.map((agent) => (
                <div
                  key={agent.mtp_id}
                  className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/20 rounded-lg"
                >
                  <div>
                    <Link to={`/agents/${agent.mtp_id}`} className="text-blue-400 hover:text-blue-300 font-mono text-sm">
                      {agent.mtp_id}
                    </Link>
                    <p className="text-xs text-slate-500">{agent.org}</p>
                    <p className="text-xs text-red-400 mt-1">{agent.reason}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-bold ${getTrustScoreColor(agent.score)}`}>
                      {agent.score}
                    </p>
                    <div className="flex items-center gap-1 text-xs text-red-400">
                      <TrendingDown className="h-3 w-3" />
                      {agent.change}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4 border-slate-700 text-slate-400">
              View All At-Risk Agents
            </Button>
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-green-400" />
              Top Performers
            </CardTitle>
            <CardDescription className="text-slate-400">Agents with highest trust scores</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {TOP_PERFORMERS.map((agent, index) => (
                <div
                  key={agent.mtp_id}
                  className="flex items-center justify-between p-3 bg-green-500/5 border border-green-500/20 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white font-bold text-sm">
                      #{index + 1}
                    </div>
                    <div>
                      <Link to={`/agents/${agent.mtp_id}`} className="text-blue-400 hover:text-blue-300 font-mono text-sm">
                        {agent.mtp_id}
                      </Link>
                      <p className="text-xs text-slate-500">{agent.org}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-bold ${getTrustScoreColor(agent.score)}`}>
                      {agent.score}
                    </p>
                    <div className="flex items-center gap-1 text-xs text-green-400">
                      <TrendingUp className="h-3 w-3" />
                      +{agent.change}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4 border-slate-700 text-slate-400">
              View Leaderboard
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
