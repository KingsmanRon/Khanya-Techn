/**
 * Agent Detail Page
 * Detailed view of a single agent with activity, trust score, and certifications
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  ArrowLeft,
  Activity,
  TrendingUp,
  Award,
  Clock,
  AlertTriangle,
  CheckCircle,
  Pause,
  Play,
  KeyRound,
  Copy,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Progress } from '../../components/ui/progress';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { agentAPI, auditAPI, trustAPI, certificationAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

// Sample data
const SAMPLE_AGENT = {
  mtp_id: 'MTP-a3f5b2-7k9m2p',
  agent_type: 'customer_service',
  base_model: 'Claude 3.5 Sonnet',
  status: 'ACTIVE',
  trust_score: 850,
  org: 'First National Bank',
  org_id: 'org-fnb-001',
  created_at: '2024-01-15T10:30:00Z',
  public_key: 'ed25519:7Kt3Hq9xPmNwVcR2...truncated',
  description: 'Customer service chatbot handling account inquiries and basic transactions',
  capabilities: ['account_inquiry', 'balance_check', 'transaction_history', 'fund_transfer_small'],
  mandate: {
    max_transaction_value: 10000,
    allowed_operations: ['read', 'transfer_small'],
    restricted_hours: null,
  },
};

const SAMPLE_TRUST_HISTORY = [
  { date: '2024-01-15', score: 500 },
  { date: '2024-01-22', score: 620 },
  { date: '2024-01-29', score: 710 },
  { date: '2024-02-05', score: 680 },
  { date: '2024-02-12', score: 750 },
  { date: '2024-02-19', score: 820 },
  { date: '2024-02-26', score: 850 },
];

const SAMPLE_ACTIVITIES = [
  { id: 1, type: 'TRANSACTION', description: 'Transfer R2,500 to account ***4521', status: 'SUCCESS', timestamp: '2024-02-26T10:32:00Z' },
  { id: 2, type: 'DECISION', description: 'Account balance inquiry processed', status: 'SUCCESS', timestamp: '2024-02-26T10:28:00Z' },
  { id: 3, type: 'TRANSACTION', description: 'Transfer R500 to account ***7832', status: 'SUCCESS', timestamp: '2024-02-26T10:15:00Z' },
  { id: 4, type: 'POLICY_VIOLATION', description: 'Attempted transfer exceeding daily limit', status: 'BLOCKED', timestamp: '2024-02-26T09:45:00Z' },
  { id: 5, type: 'DECISION', description: 'Customer identity verified', status: 'SUCCESS', timestamp: '2024-02-26T09:30:00Z' },
];

const SAMPLE_CERTIFICATIONS = [
  { type: 'ZA-FIN', name: 'South African Financial Services', status: 'CERTIFIED', issued_at: '2024-01-20', expires_at: '2025-01-20' },
  { type: 'POPIA', name: 'POPIA Compliance', status: 'CERTIFIED', issued_at: '2024-01-22', expires_at: '2025-01-22' },
  { type: 'EU-AI', name: 'EU AI Act Compliance', status: 'PENDING', issued_at: null, expires_at: null },
];

export default function AgentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [agent, setAgent] = useState(null);
  const [trustHistory, setTrustHistory] = useState([]);
  const [activities, setActivities] = useState([]);
  const [certifications, setCertifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchAgentData();
  }, [id]);

  const fetchAgentData = async () => {
    try {
      // Fetch agent details
      const agentRes = await agentAPI.get(id).catch(() => null);
      setAgent(agentRes?.data || { ...SAMPLE_AGENT, mtp_id: id });

      // Fetch trust history
      const trustRes = await trustAPI.getHistory(id).catch(() => null);
      setTrustHistory(trustRes?.data || SAMPLE_TRUST_HISTORY);

      // Fetch activities
      const activityRes = await auditAPI.getByAgent(id, { limit: 10 }).catch(() => null);
      setActivities(activityRes?.data || SAMPLE_ACTIVITIES);

      // Fetch certifications
      const certRes = await certificationAPI.list(id).catch(() => null);
      setCertifications(certRes?.data || SAMPLE_CERTIFICATIONS);
    } catch (error) {
      console.error('Failed to fetch agent data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async () => {
    setActionLoading(true);
    try {
      await agentAPI.suspend(id, 'Manual suspension');
      setAgent(prev => ({ ...prev, status: 'SUSPENDED' }));
    } catch (error) {
      console.error('Failed to suspend agent:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async () => {
    setActionLoading(true);
    try {
      await agentAPI.activate(id);
      setAgent(prev => ({ ...prev, status: 'ACTIVE' }));
    } catch (error) {
      console.error('Failed to activate agent:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusBadge = (status) => {
    const variants = {
      ACTIVE: 'bg-green-500/10 text-green-400 border-green-500/20',
      SUSPENDED: 'bg-red-500/10 text-red-400 border-red-500/20',
      PENDING: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      SUCCESS: 'bg-green-500/10 text-green-400 border-green-500/20',
      BLOCKED: 'bg-red-500/10 text-red-400 border-red-500/20',
      CERTIFIED: 'bg-green-500/10 text-green-400 border-green-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const getTrustScoreColor = (score) => {
    if (score >= 800) return 'text-green-400';
    if (score >= 600) return 'text-blue-400';
    if (score >= 400) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold text-white">Agent not found</h2>
        <p className="text-slate-400 mt-2">The agent with ID {id} could not be found.</p>
        <Button asChild className="mt-4">
          <Link to="/agents">Back to Agents</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/agents')}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white font-mono">{agent.mtp_id}</h1>
              <Badge variant="outline" className={getStatusBadge(agent.status)}>
                {agent.status}
              </Badge>
            </div>
            <p className="text-slate-400 mt-1">{agent.org} - {agent.agent_type}</p>
          </div>
        </div>
        {hasPermission('manage:agents') && (
          <div className="flex gap-2">
            {agent.status === 'ACTIVE' ? (
              <Button
                variant="outline"
                onClick={handleSuspend}
                disabled={actionLoading}
                className="border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10"
              >
                {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Pause className="h-4 w-4 mr-2" />}
                Suspend
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={handleActivate}
                disabled={actionLoading}
                className="border-green-500/50 text-green-400 hover:bg-green-500/10"
              >
                {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                Reactivate
              </Button>
            )}
            <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10">
              <KeyRound className="h-4 w-4 mr-2" />
              Revoke Keys
            </Button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Trust Score</p>
                <p className={`text-2xl font-bold ${getTrustScoreColor(agent.trust_score)}`}>
                  {agent.trust_score}/1000
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Activity className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Today's Activity</p>
                <p className="text-2xl font-bold text-white">247</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Award className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Certifications</p>
                <p className="text-2xl font-bold text-white">
                  {certifications.filter(c => c.status === 'CERTIFIED').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Registered</p>
                <p className="text-lg font-bold text-white">
                  {new Date(agent.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="overview" className="data-[state=active]:bg-blue-600">Overview</TabsTrigger>
          <TabsTrigger value="activity" className="data-[state=active]:bg-blue-600">Activity</TabsTrigger>
          <TabsTrigger value="trust" className="data-[state=active]:bg-blue-600">Trust Score</TabsTrigger>
          <TabsTrigger value="certifications" className="data-[state=active]:bg-blue-600">Certifications</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Agent Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-400">MTP ID</span>
                  <div className="flex items-center gap-2">
                    <code className="text-blue-400 font-mono">{agent.mtp_id}</code>
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => copyToClipboard(agent.mtp_id)}>
                      <Copy className="h-3 w-3 text-slate-400" />
                    </Button>
                  </div>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-400">Type</span>
                  <span className="text-white">{agent.agent_type}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-400">Base Model</span>
                  <span className="text-white">{agent.base_model}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-400">Organization</span>
                  <span className="text-white">{agent.org}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-slate-400">Description</span>
                  <span className="text-white text-right max-w-[60%]">{agent.description}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Mandate & Capabilities</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-slate-400 text-sm mb-2">Capabilities</p>
                  <div className="flex flex-wrap gap-2">
                    {agent.capabilities?.map((cap) => (
                      <Badge key={cap} variant="outline" className="bg-slate-700/50 text-slate-300 border-slate-600">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="pt-4 border-t border-slate-700">
                  <p className="text-slate-400 text-sm mb-2">Transaction Limit</p>
                  <p className="text-2xl font-bold text-white">
                    R{agent.mandate?.max_transaction_value?.toLocaleString() || 'N/A'}
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-700">
                  <p className="text-slate-400 text-sm mb-2">Allowed Operations</p>
                  <div className="flex flex-wrap gap-2">
                    {agent.mandate?.allowed_operations?.map((op) => (
                      <Badge key={op} variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20">
                        {op}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-400" />
                Recent Activity
              </CardTitle>
              <CardDescription className="text-slate-400">Latest audit events for this agent</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-4 p-4 bg-slate-700/30 rounded-lg">
                    <div className={`p-2 rounded-lg ${activity.status === 'BLOCKED' ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                      {activity.status === 'BLOCKED' ? (
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-white font-medium">{activity.description}</p>
                        <Badge variant="outline" className={getStatusBadge(activity.status)}>
                          {activity.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                        <span>{activity.type}</span>
                        <span>-</span>
                        <span>{new Date(activity.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4 border-slate-700 text-slate-400">
                View Full Audit Trail
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trust Score Tab */}
        <TabsContent value="trust">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                Trust Score History
              </CardTitle>
              <CardDescription className="text-slate-400">Score progression over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trustHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} domain={[0, 1000]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                  />
                </LineChart>
              </ResponsiveContainer>

              {/* Trust Score Breakdown */}
              <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm">Reliability</p>
                  <p className="text-xl font-bold text-green-400 mt-1">85%</p>
                  <Progress value={85} className="mt-2 h-1" />
                </div>
                <div className="p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm">Compliance</p>
                  <p className="text-xl font-bold text-blue-400 mt-1">92%</p>
                  <Progress value={92} className="mt-2 h-1" />
                </div>
                <div className="p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm">Transparency</p>
                  <p className="text-xl font-bold text-yellow-400 mt-1">78%</p>
                  <Progress value={78} className="mt-2 h-1" />
                </div>
                <div className="p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm">History</p>
                  <p className="text-xl font-bold text-purple-400 mt-1">88%</p>
                  <Progress value={88} className="mt-2 h-1" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Certifications Tab */}
        <TabsContent value="certifications">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="h-5 w-5 text-purple-400" />
                Certifications
              </CardTitle>
              <CardDescription className="text-slate-400">Compliance certifications for this agent</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {certifications.map((cert) => (
                  <div key={cert.type} className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className={getStatusBadge(cert.status)}>
                        {cert.status}
                      </Badge>
                      <span className="text-xs text-slate-500">{cert.type}</span>
                    </div>
                    <h3 className="text-white font-medium">{cert.name}</h3>
                    {cert.status === 'CERTIFIED' && (
                      <p className="text-xs text-slate-400 mt-2">
                        Expires: {new Date(cert.expires_at).toLocaleDateString()}
                      </p>
                    )}
                    {cert.status === 'PENDING' && (
                      <Button variant="outline" size="sm" className="mt-3 w-full border-slate-600 text-slate-300">
                        Check Status
                      </Button>
                    )}
                  </div>
                ))}
              </div>
              <Button className="mt-4 bg-blue-600 hover:bg-blue-700">
                Apply for Certification
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
