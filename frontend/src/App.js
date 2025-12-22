import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { Shield, Lock, Database, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [agents, setAgents] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemStatus();
    fetchSampleData();
    
    const interval = setInterval(() => {
      fetchSystemStatus();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/health`);
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const fetchSampleData = async () => {
    setLoading(false);
    setAgents([
      {
        mtp_id: 'MTP-a3f5b2-7k9m2p',
        agent_type: 'customer_service',
        base_model: 'Claude 3.5 Sonnet',
        status: 'ACTIVE',
        trust_score: 850,
        org: 'First National Bank'
      },
      {
        mtp_id: 'MTP-b4c6d3-8l0n3q',
        agent_type: 'fraud_detection',
        base_model: 'GPT-4',
        status: 'ACTIVE',
        trust_score: 920,
        org: 'Standard Bank'
      },
      {
        mtp_id: 'MTP-c5d7e4-9m1o4r',
        agent_type: 'trading_bot',
        base_model: 'Custom Model',
        status: 'SUSPENDED',
        trust_score: 450,
        org: 'Investment Corp'
      }
    ]);
    
    setAuditEvents([
      {
        event_id: 'evt-001',
        mtp_id: 'MTP-a3f5b2-7k9m2p',
        timestamp: new Date().toISOString(),
        event_type: 'TRANSACTION',
        action_description: 'Transfer R500 from Account A to Account B',
        status: 'SUCCESS',
        value: 500
      },
      {
        event_id: 'evt-002',
        mtp_id: 'MTP-b4c6d3-8l0n3q',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        event_type: 'DECISION',
        action_description: 'Flagged suspicious transaction',
        status: 'SUCCESS',
        value: null
      },
      {
        event_id: 'evt-003',
        mtp_id: 'MTP-c5d7e4-9m1o4r',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        event_type: 'POLICY_VIOLATION',
        action_description: 'Exceeded transaction limit',
        status: 'BLOCKED',
        value: 50000
      }
    ]);
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'ACTIVE': return 'text-green-600';
      case 'SUSPENDED': return 'text-red-600';
      case 'PENDING': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getEventStatusColor = (status) => {
    switch(status) {
      case 'SUCCESS': return 'text-green-600';
      case 'BLOCKED': return 'text-red-600';
      case 'FAILURE': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  const getTrustScoreColor = (score) => {
    if (score >= 800) return 'text-green-600 bg-green-50';
    if (score >= 500) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">Machine Trust Protocol</h1>
                <p className="text-sm text-slate-400">Basel III for AI Agents</p>
              </div>
            </div>
            
            {systemStatus && (
              <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-400 font-medium">System Operational</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Shield className="h-5 w-5 text-blue-400" />
              </div>
              <h3 className="text-sm font-medium text-slate-400">Active Agents</h3>
            </div>
            <p className="text-3xl font-bold text-white">{agents.filter(a => a.status === 'ACTIVE').length}</p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
              <h3 className="text-sm font-medium text-slate-400">Requests Today</h3>
            </div>
            <p className="text-3xl font-bold text-white">1,247</p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-red-500/10 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <h3 className="text-sm font-medium text-slate-400">Blocked Requests</h3>
            </div>
            <p className="text-3xl font-bold text-white">23</p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Database className="h-5 w-5 text-purple-400" />
              </div>
              <h3 className="text-sm font-medium text-slate-400">Blockchain Anchors</h3>
            </div>
            <p className="text-3xl font-bold text-white">87</p>
          </div>
        </div>

        {/* Agent Registry */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="h-6 w-6 text-blue-400" />
            <h2 className="text-xl font-bold text-white">Agent Registry</h2>
          </div>
          
          {loading ? (
            <p className="text-slate-400">Loading...</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">MTP ID</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Model</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Organization</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Trust Score</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {agents.map((agent) => (
                    <tr key={agent.mtp_id} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                      <td className="py-4 px-4">
                        <code className="text-sm text-blue-400 font-mono">{agent.mtp_id}</code>
                      </td>
                      <td className="py-4 px-4 text-sm text-slate-300">{agent.agent_type}</td>
                      <td className="py-4 px-4 text-sm text-slate-300">{agent.base_model}</td>
                      <td className="py-4 px-4 text-sm text-slate-300">{agent.org}</td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getTrustScoreColor(agent.trust_score)}`}>
                          {agent.trust_score}/1000
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`text-sm font-medium ${getStatusColor(agent.status)}`}>
                          {agent.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Audit Trail */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <Activity className="h-6 w-6 text-green-400" />
            <h2 className="text-xl font-bold text-white">Recent Audit Events</h2>
            <span className="ml-auto text-xs text-slate-400">Live updating every 5s</span>
          </div>
          
          <div className="space-y-4">
            {auditEvents.map((event) => (
              <div key={event.event_id} className="bg-slate-700/30 border border-slate-600/50 rounded-lg p-4 hover:bg-slate-700/50 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <code className="text-sm text-blue-400 font-mono">{event.mtp_id}</code>
                    <span className="text-xs text-slate-400">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <span className={`text-sm font-medium ${getEventStatusColor(event.status)}`}>
                    {event.status}
                  </span>
                </div>
                <p className="text-sm text-slate-300 mb-2">{event.action_description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span>Type: {event.event_type}</span>
                  {event.value && <span>Value: R{event.value.toLocaleString()}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <p className="text-slate-400 text-sm mb-2">
            Machine Trust Protocol v0.1.0 - Core Enforcement System
          </p>
          <p className="text-slate-500 text-xs">
            Powered by PostgreSQL + TimescaleDB + Base L2 Blockchain
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
