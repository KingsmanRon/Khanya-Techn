/**
 * Audit Trail Explorer
 * Search, filter, and explore audit events
 */
import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  ScrollText,
  Search,
  Filter,
  Calendar,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Eye,
  Loader2,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { auditAPI } from '../services/api';

// Sample audit events
const SAMPLE_EVENTS = [
  { event_id: 'evt-001', mtp_id: 'MTP-a3f5b2-7k9m2p', event_type: 'TRANSACTION', action_description: 'Transfer R2,500 to account ***4521', status: 'SUCCESS', timestamp: '2024-02-26T10:32:00Z', metadata: { amount: 2500, target_account: '***4521' } },
  { event_id: 'evt-002', mtp_id: 'MTP-b4c6d3-8l0n3q', event_type: 'DECISION', action_description: 'Flagged suspicious activity on account ***7832', status: 'SUCCESS', timestamp: '2024-02-26T10:28:00Z', metadata: { risk_score: 0.85 } },
  { event_id: 'evt-003', mtp_id: 'MTP-c5d7e4-9m1o4r', event_type: 'POLICY_VIOLATION', action_description: 'Attempted transfer exceeding daily limit', status: 'BLOCKED', timestamp: '2024-02-26T10:15:00Z', metadata: { attempted_amount: 150000, limit: 100000 } },
  { event_id: 'evt-004', mtp_id: 'MTP-d6e8f5-0n2p5s', event_type: 'TRANSACTION', action_description: 'Document verification completed', status: 'SUCCESS', timestamp: '2024-02-26T10:10:00Z', metadata: { document_type: 'ID', verified: true } },
  { event_id: 'evt-005', mtp_id: 'MTP-a3f5b2-7k9m2p', event_type: 'TRANSACTION', action_description: 'Balance inquiry processed', status: 'SUCCESS', timestamp: '2024-02-26T10:05:00Z', metadata: {} },
  { event_id: 'evt-006', mtp_id: 'MTP-e7f9g6-1o3q6t', event_type: 'DECISION', action_description: 'Risk assessment for loan application', status: 'SUCCESS', timestamp: '2024-02-26T10:00:00Z', metadata: { risk_level: 'LOW', recommendation: 'APPROVE' } },
  { event_id: 'evt-007', mtp_id: 'MTP-b4c6d3-8l0n3q', event_type: 'AUTHENTICATION', action_description: 'Agent session started', status: 'SUCCESS', timestamp: '2024-02-26T09:55:00Z', metadata: {} },
  { event_id: 'evt-008', mtp_id: 'MTP-c5d7e4-9m1o4r', event_type: 'POLICY_VIOLATION', action_description: 'Attempted operation outside business hours', status: 'BLOCKED', timestamp: '2024-02-26T06:30:00Z', metadata: { attempted_time: '06:30', allowed_start: '08:00' } },
  { event_id: 'evt-009', mtp_id: 'MTP-a3f5b2-7k9m2p', event_type: 'TRANSACTION', action_description: 'Transfer R500 to account ***9123', status: 'SUCCESS', timestamp: '2024-02-25T16:45:00Z', metadata: { amount: 500 } },
  { event_id: 'evt-010', mtp_id: 'MTP-d6e8f5-0n2p5s', event_type: 'DECISION', action_description: 'Customer identity verification', status: 'SUCCESS', timestamp: '2024-02-25T15:30:00Z', metadata: { method: 'biometric' } },
];

const EVENT_TYPES = ['ALL', 'TRANSACTION', 'DECISION', 'POLICY_VIOLATION', 'AUTHENTICATION', 'ERROR'];
const STATUSES = ['ALL', 'SUCCESS', 'BLOCKED', 'FAILURE', 'PENDING'];

export default function Audit() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [dateFilter, setDateFilter] = useState('today');
  const [page, setPage] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const pageSize = 10;

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await auditAPI.list({ limit: 100 });
      if (Array.isArray(response.data) && response.data.length > 0) {
        setEvents(response.data);
      } else {
        setEvents(SAMPLE_EVENTS);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setEvents(SAMPLE_EVENTS);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchesSearch = !searchQuery ||
        event.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        event.mtp_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        event.action_description?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType = typeFilter === 'ALL' || event.event_type === typeFilter;
      const matchesStatus = statusFilter === 'ALL' || event.status === statusFilter;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [events, searchQuery, typeFilter, statusFilter]);

  const paginatedEvents = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredEvents.slice(start, start + pageSize);
  }, [filteredEvents, page]);

  const totalPages = Math.ceil(filteredEvents.length / pageSize);

  const stats = useMemo(() => ({
    total: events.length,
    success: events.filter(e => e.status === 'SUCCESS').length,
    blocked: events.filter(e => e.status === 'BLOCKED').length,
    violations: events.filter(e => e.event_type === 'POLICY_VIOLATION').length,
  }), [events]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'SUCCESS': return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'BLOCKED': return <XCircle className="h-4 w-4 text-red-400" />;
      case 'FAILURE': return <AlertTriangle className="h-4 w-4 text-orange-400" />;
      default: return <Clock className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      SUCCESS: 'bg-green-500/10 text-green-400 border-green-500/20',
      BLOCKED: 'bg-red-500/10 text-red-400 border-red-500/20',
      FAILURE: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      PENDING: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const getTypeBadge = (type) => {
    const variants = {
      TRANSACTION: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      DECISION: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      POLICY_VIOLATION: 'bg-red-500/10 text-red-400 border-red-500/20',
      AUTHENTICATION: 'bg-green-500/10 text-green-400 border-green-500/20',
      ERROR: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    };
    return variants[type] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const exportToCSV = () => {
    const headers = ['Event ID', 'MTP ID', 'Type', 'Description', 'Status', 'Timestamp'];
    const rows = filteredEvents.map(e => [
      e.event_id, e.mtp_id, e.event_type, e.action_description, e.status, e.timestamp
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audit_events.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Trail</h1>
          <p className="text-slate-400">Explore and analyze audit events</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={fetchEvents} className="border-slate-700 text-slate-400">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline" onClick={exportToCSV} className="border-slate-700 text-slate-400">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <ScrollText className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Events</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
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
                <p className="text-sm text-slate-400">Successful</p>
                <p className="text-2xl font-bold text-white">{stats.success}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 rounded-lg">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Blocked</p>
                <p className="text-2xl font-bold text-white">{stats.blocked}</p>
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
                <p className="text-sm text-slate-400">Violations</p>
                <p className="text-2xl font-bold text-white">{stats.violations}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by event ID, agent ID, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-900/50 border-slate-700 text-white"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[160px] bg-slate-900/50 border-slate-700 text-white">
                <SelectValue placeholder="Event Type" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {EVENT_TYPES.map(type => (
                  <SelectItem key={type} value={type}>{type === 'ALL' ? 'All Types' : type}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px] bg-slate-900/50 border-slate-700 text-white">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {STATUSES.map(status => (
                  <SelectItem key={status} value={status}>{status === 'ALL' ? 'All Status' : status}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={dateFilter} onValueChange={setDateFilter}>
              <SelectTrigger className="w-[140px] bg-slate-900/50 border-slate-700 text-white">
                <Calendar className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Date" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Events Table */}
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
                    <TableHead className="text-slate-400">Event ID</TableHead>
                    <TableHead className="text-slate-400">Agent</TableHead>
                    <TableHead className="text-slate-400">Type</TableHead>
                    <TableHead className="text-slate-400">Description</TableHead>
                    <TableHead className="text-slate-400">Status</TableHead>
                    <TableHead className="text-slate-400">Timestamp</TableHead>
                    <TableHead className="text-slate-400 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedEvents.map((event) => (
                    <TableRow key={event.event_id} className="border-slate-700 hover:bg-slate-700/30">
                      <TableCell className="font-mono text-sm text-slate-300">{event.event_id}</TableCell>
                      <TableCell>
                        <Link to={`/agents/${event.mtp_id}`} className="text-blue-400 hover:text-blue-300 font-mono text-sm">
                          {event.mtp_id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getTypeBadge(event.event_type)}>
                          {event.event_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-300 max-w-[300px] truncate">
                        {event.action_description}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(event.status)}
                          <Badge variant="outline" className={getStatusBadge(event.status)}>
                            {event.status}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {new Date(event.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setSelectedEvent(event)}
                          className="text-slate-400 hover:text-white"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700">
                <p className="text-sm text-slate-400">
                  Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, filteredEvents.length)} of {filteredEvents.length} events
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

      {/* Event Detail Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">Event Details</DialogTitle>
          </DialogHeader>
          {selectedEvent && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-slate-400 text-sm">Event ID</p>
                  <p className="text-white font-mono">{selectedEvent.event_id}</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Agent</p>
                  <Link to={`/agents/${selectedEvent.mtp_id}`} className="text-blue-400 font-mono">
                    {selectedEvent.mtp_id}
                  </Link>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Type</p>
                  <Badge variant="outline" className={getTypeBadge(selectedEvent.event_type)}>
                    {selectedEvent.event_type}
                  </Badge>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Status</p>
                  <Badge variant="outline" className={getStatusBadge(selectedEvent.status)}>
                    {selectedEvent.status}
                  </Badge>
                </div>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Description</p>
                <p className="text-white">{selectedEvent.action_description}</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Timestamp</p>
                <p className="text-white">{new Date(selectedEvent.timestamp).toLocaleString()}</p>
              </div>
              {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                <div>
                  <p className="text-slate-400 text-sm mb-2">Metadata</p>
                  <pre className="bg-slate-900 p-3 rounded-lg text-sm text-slate-300 overflow-auto">
                    {JSON.stringify(selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
