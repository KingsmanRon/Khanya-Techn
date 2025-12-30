/**
 * Agent List Page
 * Registry of all MTP agents with search, filter, and actions
 */
import React, { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Shield,
  Search,
  Filter,
  Plus,
  MoreVertical,
  Eye,
  Pause,
  Play,
  KeyRound,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import { agentAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

// Sample agents for demo
const SAMPLE_AGENTS = [
  { mtp_id: 'MTP-a3f5b2-7k9m2p', agent_type: 'customer_service', base_model: 'Claude 3.5 Sonnet', status: 'ACTIVE', trust_score: 850, org: 'First National Bank', created_at: '2024-01-15' },
  { mtp_id: 'MTP-b4c6d3-8l0n3q', agent_type: 'fraud_detection', base_model: 'GPT-4', status: 'ACTIVE', trust_score: 920, org: 'Standard Bank', created_at: '2024-01-10' },
  { mtp_id: 'MTP-c5d7e4-9m1o4r', agent_type: 'trading_bot', base_model: 'Custom Model', status: 'SUSPENDED', trust_score: 450, org: 'Investment Corp', created_at: '2024-01-08' },
  { mtp_id: 'MTP-d6e8f5-0n2p5s', agent_type: 'doc_processor', base_model: 'Claude 3 Opus', status: 'ACTIVE', trust_score: 780, org: 'Nedbank', created_at: '2024-01-05' },
  { mtp_id: 'MTP-e7f9g6-1o3q6t', agent_type: 'risk_assessment', base_model: 'GPT-4 Turbo', status: 'ACTIVE', trust_score: 890, org: 'Absa Group', created_at: '2024-01-03' },
  { mtp_id: 'MTP-f8g0h7-2p4r7u', agent_type: 'customer_service', base_model: 'Gemini Pro', status: 'PENDING', trust_score: 0, org: 'Capitec', created_at: '2024-01-20' },
  { mtp_id: 'MTP-g9h1i8-3q5s8v', agent_type: 'fraud_detection', base_model: 'Claude 3.5 Sonnet', status: 'ACTIVE', trust_score: 870, org: 'Discovery Bank', created_at: '2023-12-28' },
  { mtp_id: 'MTP-h0i2j9-4r6t9w', agent_type: 'trading_bot', base_model: 'Custom Model', status: 'ACTIVE', trust_score: 720, org: 'African Bank', created_at: '2023-12-20' },
  { mtp_id: 'MTP-i1j3k0-5s7u0x', agent_type: 'doc_processor', base_model: 'GPT-4', status: 'ACTIVE', trust_score: 810, org: 'Investec', created_at: '2023-12-15' },
  { mtp_id: 'MTP-j2k4l1-6t8v1y', agent_type: 'risk_assessment', base_model: 'Claude 3 Opus', status: 'SUSPENDED', trust_score: 380, org: 'TymeBank', created_at: '2023-12-10' },
];

export default function AgentList() {
  const [searchParams] = useSearchParams();
  const { hasPermission } = useAuth();

  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [suspendDialog, setSuspendDialog] = useState({ open: false, agent: null });
  const [actionLoading, setActionLoading] = useState(false);

  const pageSize = 10;

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await agentAPI.list();
      if (Array.isArray(response.data) && response.data.length > 0) {
        setAgents(response.data);
      } else {
        setAgents(SAMPLE_AGENTS);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      setAgents(SAMPLE_AGENTS);
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesSearch = !searchQuery ||
        agent.mtp_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.org?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.agent_type?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
      const matchesType = typeFilter === 'all' || agent.agent_type === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [agents, searchQuery, statusFilter, typeFilter]);

  const paginatedAgents = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredAgents.slice(start, start + pageSize);
  }, [filteredAgents, page]);

  const totalPages = Math.ceil(filteredAgents.length / pageSize);

  const agentTypes = [...new Set(agents.map(a => a.agent_type))];

  const handleSuspend = async () => {
    if (!suspendDialog.agent) return;
    setActionLoading(true);
    try {
      await agentAPI.suspend(suspendDialog.agent.mtp_id, 'Manual suspension');
      setAgents(prev => prev.map(a =>
        a.mtp_id === suspendDialog.agent.mtp_id
          ? { ...a, status: 'SUSPENDED' }
          : a
      ));
    } catch (error) {
      console.error('Failed to suspend agent:', error);
    } finally {
      setActionLoading(false);
      setSuspendDialog({ open: false, agent: null });
    }
  };

  const handleActivate = async (agent) => {
    try {
      await agentAPI.activate(agent.mtp_id);
      setAgents(prev => prev.map(a =>
        a.mtp_id === agent.mtp_id
          ? { ...a, status: 'ACTIVE' }
          : a
      ));
    } catch (error) {
      console.error('Failed to activate agent:', error);
    }
  };

  const getTrustScoreColor = (score) => {
    if (score >= 800) return 'text-green-400 bg-green-500/10';
    if (score >= 600) return 'text-blue-400 bg-blue-500/10';
    if (score >= 400) return 'text-yellow-400 bg-yellow-500/10';
    return 'text-red-400 bg-red-500/10';
  };

  const getStatusBadge = (status) => {
    const variants = {
      ACTIVE: 'bg-green-500/10 text-green-400 border-green-500/20',
      SUSPENDED: 'bg-red-500/10 text-red-400 border-red-500/20',
      PENDING: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const exportToCSV = () => {
    const headers = ['MTP ID', 'Type', 'Model', 'Organization', 'Status', 'Trust Score', 'Created'];
    const rows = filteredAgents.map(a => [
      a.mtp_id, a.agent_type, a.base_model, a.org, a.status, a.trust_score, a.created_at
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agents.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Registry</h1>
          <p className="text-slate-400">Manage and monitor registered AI agents</p>
        </div>
        {hasPermission('manage:agents') && (
          <Button asChild className="bg-blue-600 hover:bg-blue-700">
            <Link to="/agents/new">
              <Plus className="h-4 w-4 mr-2" />
              Register Agent
            </Link>
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by MTP ID, organization, or type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-900/50 border-slate-700 text-white"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px] bg-slate-900/50 border-slate-700 text-white">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="SUSPENDED">Suspended</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px] bg-slate-900/50 border-slate-700 text-white">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="all">All Types</SelectItem>
                {agentTypes.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button variant="outline" size="icon" onClick={fetchAgents} className="border-slate-700 text-slate-400 hover:text-white">
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" onClick={exportToCSV} className="border-slate-700 text-slate-400 hover:text-white">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700 hover:bg-transparent">
                    <TableHead className="text-slate-400">MTP ID</TableHead>
                    <TableHead className="text-slate-400">Type</TableHead>
                    <TableHead className="text-slate-400">Model</TableHead>
                    <TableHead className="text-slate-400">Organization</TableHead>
                    <TableHead className="text-slate-400">Trust Score</TableHead>
                    <TableHead className="text-slate-400">Status</TableHead>
                    <TableHead className="text-slate-400 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedAgents.map((agent) => (
                    <TableRow key={agent.mtp_id} className="border-slate-700 hover:bg-slate-700/30">
                      <TableCell>
                        <Link to={`/agents/${agent.mtp_id}`} className="text-blue-400 hover:text-blue-300 font-mono text-sm">
                          {agent.mtp_id}
                        </Link>
                      </TableCell>
                      <TableCell className="text-slate-300">{agent.agent_type}</TableCell>
                      <TableCell className="text-slate-300">{agent.base_model}</TableCell>
                      <TableCell className="text-slate-300">{agent.org}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTrustScoreColor(agent.trust_score)}`}>
                          {agent.trust_score}/1000
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getStatusBadge(agent.status)}>
                          {agent.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                            <DropdownMenuItem asChild className="text-slate-300 hover:text-white cursor-pointer hover:bg-slate-700">
                              <Link to={`/agents/${agent.mtp_id}`}>
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </Link>
                            </DropdownMenuItem>
                            {hasPermission('manage:agents') && (
                              <>
                                <DropdownMenuSeparator className="bg-slate-700" />
                                {agent.status === 'ACTIVE' ? (
                                  <DropdownMenuItem
                                    onClick={() => setSuspendDialog({ open: true, agent })}
                                    className="text-yellow-400 hover:text-yellow-300 cursor-pointer hover:bg-slate-700"
                                  >
                                    <Pause className="h-4 w-4 mr-2" />
                                    Suspend Agent
                                  </DropdownMenuItem>
                                ) : agent.status === 'SUSPENDED' && (
                                  <DropdownMenuItem
                                    onClick={() => handleActivate(agent)}
                                    className="text-green-400 hover:text-green-300 cursor-pointer hover:bg-slate-700"
                                  >
                                    <Play className="h-4 w-4 mr-2" />
                                    Reactivate
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuItem className="text-red-400 hover:text-red-300 cursor-pointer hover:bg-slate-700">
                                  <KeyRound className="h-4 w-4 mr-2" />
                                  Revoke Keys
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700">
                <p className="text-sm text-slate-400">
                  Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, filteredAgents.length)} of {filteredAgents.length} agents
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-slate-700 text-slate-400"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-slate-400">
                    Page {page} of {totalPages || 1}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="border-slate-700 text-slate-400"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Suspend Confirmation Dialog */}
      <Dialog open={suspendDialog.open} onOpenChange={(open) => setSuspendDialog({ open, agent: null })}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Suspend Agent</DialogTitle>
            <DialogDescription className="text-slate-400">
              Are you sure you want to suspend agent <code className="text-blue-400">{suspendDialog.agent?.mtp_id}</code>?
              This will immediately block all requests from this agent.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSuspendDialog({ open: false, agent: null })}
              className="border-slate-700 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSuspend}
              disabled={actionLoading}
              className="bg-red-600 hover:bg-red-700"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Suspend Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
