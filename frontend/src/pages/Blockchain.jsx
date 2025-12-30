/**
 * Blockchain Explorer
 * View Merkle batches and anchoring status
 */
import React, { useState, useEffect } from 'react';
import {
  Blocks,
  Link2,
  CheckCircle,
  Clock,
  ExternalLink,
  Copy,
  RefreshCw,
  Loader2,
  Hash,
  Layers,
  Activity,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { blockchainAPI } from '../services/api';

const SAMPLE_BATCHES = [
  {
    batch_id: 87,
    merkle_root: '0x7a3f8b2c9d4e5f6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a',
    event_count: 100,
    status: 'ANCHORED',
    tx_hash: '0x8f2a9c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
    block_number: 12345678,
    timestamp: '2024-02-26T10:30:00Z',
    gas_used: 45000,
  },
  {
    batch_id: 86,
    merkle_root: '0x6b2e7a1d8c3f4e5a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
    event_count: 100,
    status: 'ANCHORED',
    tx_hash: '0x7e1b8c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
    block_number: 12345123,
    timestamp: '2024-02-26T10:25:00Z',
    gas_used: 44500,
  },
  {
    batch_id: 85,
    merkle_root: '0x5a1d6b0c9e8f7a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6',
    event_count: 100,
    status: 'ANCHORED',
    tx_hash: '0x6d0a7b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9',
    block_number: 12344567,
    timestamp: '2024-02-26T10:20:00Z',
    gas_used: 45200,
  },
  {
    batch_id: 84,
    merkle_root: '0x4f0c5a9b8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1',
    event_count: 100,
    status: 'ANCHORED',
    tx_hash: '0x5c9f6a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8',
    block_number: 12344000,
    timestamp: '2024-02-26T10:15:00Z',
    gas_used: 44800,
  },
];

export default function Blockchain() {
  const [loading, setLoading] = useState(true);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [pendingEvents, setPendingEvents] = useState(42);
  const [nextBatchIn, setNextBatchIn] = useState(222); // seconds

  useEffect(() => {
    fetchBatches();
  }, []);

  useEffect(() => {
    // Countdown timer
    const timer = setInterval(() => {
      setNextBatchIn(prev => prev > 0 ? prev - 1 : 300);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchBatches = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setBatches(SAMPLE_BATCHES);
    } catch (error) {
      console.error('Failed to fetch batches:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const truncateHash = (hash) => {
    if (!hash) return '';
    return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const stats = {
    totalBatches: batches.length + 84, // Simulated total
    totalEvents: (batches.length + 84) * 100,
    lastAnchor: batches[0]?.timestamp ? new Date(batches[0].timestamp).toLocaleTimeString() : 'N/A',
    avgGas: Math.round(batches.reduce((sum, b) => sum + b.gas_used, 0) / batches.length) || 0,
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
          <h1 className="text-2xl font-bold text-white">Blockchain Explorer</h1>
          <p className="text-slate-400">Merkle batches anchored to Base L2</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20 px-3 py-1">
            <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse mr-2" />
            Base Sepolia Connected
          </Badge>
          <Button variant="outline" onClick={fetchBatches} className="border-slate-700 text-slate-400">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Blocks className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Batches</p>
                <p className="text-2xl font-bold text-white">{stats.totalBatches}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Activity className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Events Anchored</p>
                <p className="text-2xl font-bold text-white">{stats.totalEvents.toLocaleString()}</p>
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
                <p className="text-sm text-slate-400">Last Anchor</p>
                <p className="text-2xl font-bold text-white">{stats.lastAnchor}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Hash className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Avg Gas Used</p>
                <p className="text-2xl font-bold text-white">{stats.avgGas.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Batch */}
      <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/20">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <Clock className="h-6 w-6 text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Pending Batch #{stats.totalBatches + 1}</h3>
                <p className="text-slate-400">{pendingEvents} events waiting to be anchored</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-400">Next anchor in</p>
              <p className="text-3xl font-bold text-purple-400 font-mono">{formatTime(nextBatchIn)}</p>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-400">Batch Progress</span>
              <span className="text-white">{pendingEvents}/100 events</span>
            </div>
            <Progress value={pendingEvents} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Batches Table */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-purple-400" />
            Recent Batches
          </CardTitle>
          <CardDescription className="text-slate-400">
            Merkle batches anchored to Base L2 Sepolia
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-slate-700 hover:bg-transparent">
                <TableHead className="text-slate-400">Batch</TableHead>
                <TableHead className="text-slate-400">Merkle Root</TableHead>
                <TableHead className="text-slate-400">Events</TableHead>
                <TableHead className="text-slate-400">Status</TableHead>
                <TableHead className="text-slate-400">Block</TableHead>
                <TableHead className="text-slate-400">Time</TableHead>
                <TableHead className="text-slate-400 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {batches.map((batch) => (
                <TableRow key={batch.batch_id} className="border-slate-700 hover:bg-slate-700/30">
                  <TableCell className="font-medium text-white">#{batch.batch_id}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <code className="text-purple-400 font-mono text-sm">{truncateHash(batch.merkle_root)}</code>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-slate-400 hover:text-white"
                        onClick={() => copyToClipboard(batch.merkle_root)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300">{batch.event_count}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      {batch.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-slate-300">{batch.block_number.toLocaleString()}</TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {new Date(batch.timestamp).toLocaleTimeString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedBatch(batch)}
                        className="text-slate-400 hover:text-white"
                      >
                        Details
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-slate-400 hover:text-white"
                        onClick={() => window.open(`https://sepolia.basescan.org/tx/${batch.tx_hash}`, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Batch Detail Dialog */}
      <Dialog open={!!selectedBatch} onOpenChange={() => setSelectedBatch(null)}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">Batch #{selectedBatch?.batch_id} Details</DialogTitle>
          </DialogHeader>
          {selectedBatch && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Status</p>
                  <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20 mt-1">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    {selectedBatch.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Events in Batch</p>
                  <p className="text-white font-medium">{selectedBatch.event_count}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Block Number</p>
                  <p className="text-white font-mono">{selectedBatch.block_number.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Gas Used</p>
                  <p className="text-white font-mono">{selectedBatch.gas_used.toLocaleString()}</p>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-1">Merkle Root</p>
                <div className="flex items-center gap-2 p-3 bg-slate-900 rounded-lg">
                  <code className="text-purple-400 font-mono text-sm break-all">{selectedBatch.merkle_root}</code>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-white flex-shrink-0"
                    onClick={() => copyToClipboard(selectedBatch.merkle_root)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-1">Transaction Hash</p>
                <div className="flex items-center gap-2 p-3 bg-slate-900 rounded-lg">
                  <code className="text-blue-400 font-mono text-sm break-all">{selectedBatch.tx_hash}</code>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-white flex-shrink-0"
                    onClick={() => copyToClipboard(selectedBatch.tx_hash)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-1">Timestamp</p>
                <p className="text-white">{new Date(selectedBatch.timestamp).toLocaleString()}</p>
              </div>

              <div className="flex gap-2 pt-4 border-t border-slate-700">
                <Button
                  onClick={() => window.open(`https://sepolia.basescan.org/tx/${selectedBatch.tx_hash}`, '_blank')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View on BaseScan
                </Button>
                <Button variant="outline" className="border-slate-700 text-slate-300">
                  <Hash className="h-4 w-4 mr-2" />
                  Verify Proof
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
