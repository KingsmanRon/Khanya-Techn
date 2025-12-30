/**
 * Dispute Resolution Center
 * File and manage disputes for AI agent actions
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Scale,
  Plus,
  Clock,
  CheckCircle,
  XCircle,
  MessageSquare,
  FileText,
  Upload,
  Loader2,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { disputeAPI } from '../services/api';

const SAMPLE_DISPUTES = [
  {
    id: 'DIS-001',
    agent_id: 'MTP-c5d7e4-9m1o4r',
    org: 'Investment Corp',
    type: 'UNAUTHORIZED_ACTION',
    title: 'Unauthorized trade execution',
    description: 'Agent executed a trade without proper authorization from the supervisor.',
    status: 'OPEN',
    priority: 'HIGH',
    created_at: '2024-02-25T10:00:00Z',
    updated_at: '2024-02-26T14:30:00Z',
    comments: 3,
  },
  {
    id: 'DIS-002',
    agent_id: 'MTP-a3f5b2-7k9m2p',
    org: 'First National Bank',
    type: 'INCORRECT_DECISION',
    title: 'Incorrect account classification',
    description: 'Agent classified a legitimate transaction as fraudulent.',
    status: 'IN_REVIEW',
    priority: 'MEDIUM',
    created_at: '2024-02-24T15:00:00Z',
    updated_at: '2024-02-26T09:00:00Z',
    comments: 5,
  },
  {
    id: 'DIS-003',
    agent_id: 'MTP-b4c6d3-8l0n3q',
    org: 'Standard Bank',
    type: 'DATA_BREACH',
    title: 'Potential data exposure',
    description: 'Agent may have exposed sensitive customer data in logs.',
    status: 'RESOLVED',
    priority: 'HIGH',
    created_at: '2024-02-20T08:00:00Z',
    updated_at: '2024-02-23T16:00:00Z',
    resolution: 'No data breach confirmed. Agent logging updated.',
    comments: 12,
  },
  {
    id: 'DIS-004',
    agent_id: 'MTP-d6e8f5-0n2p5s',
    org: 'Nedbank',
    type: 'SERVICE_DISRUPTION',
    title: 'Processing delay',
    description: 'Agent caused significant processing delays affecting customer transactions.',
    status: 'CLOSED',
    priority: 'LOW',
    created_at: '2024-02-18T11:00:00Z',
    updated_at: '2024-02-19T10:00:00Z',
    resolution: 'Issue was caused by external API. Agent functioned correctly.',
    comments: 4,
  },
];

const DISPUTE_TYPES = [
  { value: 'UNAUTHORIZED_ACTION', label: 'Unauthorized Action' },
  { value: 'INCORRECT_DECISION', label: 'Incorrect Decision' },
  { value: 'DATA_BREACH', label: 'Data Breach' },
  { value: 'SERVICE_DISRUPTION', label: 'Service Disruption' },
  { value: 'POLICY_VIOLATION', label: 'Policy Violation' },
  { value: 'OTHER', label: 'Other' },
];

export default function Disputes() {
  const [loading, setLoading] = useState(true);
  const [disputes, setDisputes] = useState([]);
  const [newDisputeOpen, setNewDisputeOpen] = useState(false);
  const [selectedDispute, setSelectedDispute] = useState(null);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    fetchDisputes();
  }, []);

  const fetchDisputes = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setDisputes(SAMPLE_DISPUTES);
    } catch (error) {
      console.error('Failed to fetch disputes:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDisputes = filter === 'ALL'
    ? disputes
    : disputes.filter(d => d.status === filter);

  const stats = {
    total: disputes.length,
    open: disputes.filter(d => d.status === 'OPEN').length,
    inReview: disputes.filter(d => d.status === 'IN_REVIEW').length,
    resolved: disputes.filter(d => ['RESOLVED', 'CLOSED'].includes(d.status)).length,
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'OPEN': return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
      case 'IN_REVIEW': return <Clock className="h-4 w-4 text-blue-400" />;
      case 'RESOLVED': return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'CLOSED': return <XCircle className="h-4 w-4 text-slate-400" />;
      default: return null;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      OPEN: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      IN_REVIEW: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      RESOLVED: 'bg-green-500/10 text-green-400 border-green-500/20',
      CLOSED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const getPriorityBadge = (priority) => {
    const variants = {
      HIGH: 'bg-red-500/10 text-red-400 border-red-500/20',
      MEDIUM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      LOW: 'bg-green-500/10 text-green-400 border-green-500/20',
    };
    return variants[priority] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
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
          <h1 className="text-2xl font-bold text-white">Dispute Resolution</h1>
          <p className="text-slate-400">File and manage disputes for AI agent actions</p>
        </div>
        <Button onClick={() => setNewDisputeOpen(true)} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          File Dispute
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Scale className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Disputes</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Open</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.open}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">In Review</p>
                <p className="text-2xl font-bold text-blue-400">{stats.inReview}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Resolved</p>
                <p className="text-2xl font-bold text-green-400">{stats.resolved}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['ALL', 'OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED'].map((status) => (
          <Button
            key={status}
            variant="outline"
            size="sm"
            onClick={() => setFilter(status)}
            className={filter === status
              ? 'bg-blue-600 border-blue-600 text-white'
              : 'border-slate-700 text-slate-400'
            }
          >
            {status === 'ALL' ? 'All' : status.replace('_', ' ')}
          </Button>
        ))}
      </div>

      {/* Disputes List */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-0">
          <div className="divide-y divide-slate-700">
            {filteredDisputes.map((dispute) => (
              <div
                key={dispute.id}
                className="p-4 hover:bg-slate-700/30 transition-colors cursor-pointer"
                onClick={() => setSelectedDispute(dispute)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="mt-1">
                      {getStatusIcon(dispute.status)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">{dispute.title}</span>
                        <Badge variant="outline" className={getStatusBadge(dispute.status)}>
                          {dispute.status.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline" className={getPriorityBadge(dispute.priority)}>
                          {dispute.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-400 mt-1 line-clamp-1">{dispute.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        <span className="font-mono">{dispute.id}</span>
                        <Link to={`/agents/${dispute.agent_id}`} className="text-blue-400 hover:text-blue-300 font-mono">
                          {dispute.agent_id}
                        </Link>
                        <span>{dispute.org}</span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {dispute.comments} comments
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <p>Created {new Date(dispute.created_at).toLocaleDateString()}</p>
                    <p>Updated {new Date(dispute.updated_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* New Dispute Dialog */}
      <Dialog open={newDisputeOpen} onOpenChange={setNewDisputeOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">File New Dispute</DialogTitle>
            <DialogDescription className="text-slate-400">
              Submit a dispute for review by the MTP arbitration team.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-200">Agent MTP ID</Label>
              <Input placeholder="MTP-xxxxx-xxxxx" className="bg-slate-900/50 border-slate-700 text-white" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-200">Dispute Type</Label>
              <Select>
                <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {DISPUTE_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-200">Title</Label>
              <Input placeholder="Brief description of the issue" className="bg-slate-900/50 border-slate-700 text-white" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-200">Description</Label>
              <Textarea
                placeholder="Provide detailed information about the dispute..."
                className="bg-slate-900/50 border-slate-700 text-white min-h-[100px]"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-200">Priority</Label>
              <Select>
                <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="LOW">Low</SelectItem>
                  <SelectItem value="MEDIUM">Medium</SelectItem>
                  <SelectItem value="HIGH">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="p-3 bg-slate-700/30 rounded-lg border border-dashed border-slate-600">
              <div className="flex items-center justify-center gap-2 text-slate-400">
                <Upload className="h-5 w-5" />
                <span className="text-sm">Drop files here or click to upload evidence</span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewDisputeOpen(false)} className="border-slate-700 text-slate-300">
              Cancel
            </Button>
            <Button className="bg-blue-600 hover:bg-blue-700">
              Submit Dispute
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dispute Detail Dialog */}
      <Dialog open={!!selectedDispute} onOpenChange={() => setSelectedDispute(null)}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <DialogTitle className="text-white">{selectedDispute?.title}</DialogTitle>
              {selectedDispute && (
                <Badge variant="outline" className={getStatusBadge(selectedDispute.status)}>
                  {selectedDispute.status.replace('_', ' ')}
                </Badge>
              )}
            </div>
            <DialogDescription className="text-slate-400">
              {selectedDispute?.id} - Filed on {selectedDispute && new Date(selectedDispute.created_at).toLocaleDateString()}
            </DialogDescription>
          </DialogHeader>
          {selectedDispute && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Agent</p>
                  <Link to={`/agents/${selectedDispute.agent_id}`} className="text-blue-400 font-mono">
                    {selectedDispute.agent_id}
                  </Link>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Organization</p>
                  <p className="text-white">{selectedDispute.org}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Type</p>
                  <p className="text-white">{selectedDispute.type.replace('_', ' ')}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Priority</p>
                  <Badge variant="outline" className={getPriorityBadge(selectedDispute.priority)}>
                    {selectedDispute.priority}
                  </Badge>
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Description</p>
                <p className="text-white">{selectedDispute.description}</p>
              </div>
              {selectedDispute.resolution && (
                <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <p className="text-sm text-green-400 font-medium">Resolution</p>
                  <p className="text-green-300 mt-1">{selectedDispute.resolution}</p>
                </div>
              )}
              <div className="pt-4 border-t border-slate-700">
                <p className="text-sm text-slate-400 mb-3">Timeline</p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-400" />
                    <span className="text-sm text-slate-300">Dispute filed</span>
                    <span className="text-xs text-slate-500">{new Date(selectedDispute.created_at).toLocaleString()}</span>
                  </div>
                  {selectedDispute.status !== 'OPEN' && (
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-400" />
                      <span className="text-sm text-slate-300">Under review</span>
                    </div>
                  )}
                  {['RESOLVED', 'CLOSED'].includes(selectedDispute.status) && (
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-400" />
                      <span className="text-sm text-slate-300">Resolved</span>
                      <span className="text-xs text-slate-500">{new Date(selectedDispute.updated_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedDispute(null)} className="border-slate-700 text-slate-300">
              Close
            </Button>
            {selectedDispute?.status === 'OPEN' && (
              <Button className="bg-blue-600 hover:bg-blue-700">
                <MessageSquare className="h-4 w-4 mr-2" />
                Add Comment
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
