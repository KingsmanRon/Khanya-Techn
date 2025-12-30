/**
 * Certification Center
 * Manage agent certifications and compliance
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  FileText,
  Download,
  RefreshCw,
  Loader2,
  Calendar,
  Shield,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { certificationAPI } from '../services/api';

const CERTIFICATION_TYPES = [
  {
    type: 'ZA-FIN',
    name: 'South African Financial Services',
    description: 'Compliance with SA financial regulations and FSCA requirements',
    requirements: ['Trust score >= 750', '30+ days operational', 'No policy violations in 90 days', 'KYC/AML checks passed'],
    validity: '12 months',
    icon: '🇿🇦',
  },
  {
    type: 'ZA-ECOM',
    name: 'SA E-Commerce',
    description: 'E-commerce transaction processing compliance',
    requirements: ['Trust score >= 700', 'Transaction verification enabled', 'Consumer protection protocols'],
    validity: '12 months',
    icon: '🛒',
  },
  {
    type: 'ZA-HEALTH',
    name: 'Healthcare Data',
    description: 'Healthcare data handling and PAIA compliance',
    requirements: ['Trust score >= 800', 'Data encryption verified', 'Access logging enabled', 'PAIA compliance'],
    validity: '12 months',
    icon: '🏥',
  },
  {
    type: 'EU-AI',
    name: 'EU AI Act Compliance',
    description: 'Compliance with European Union AI regulations',
    requirements: ['Trust score >= 850', 'Transparency requirements met', 'Human oversight protocols', 'Risk assessment completed'],
    validity: '24 months',
    icon: '🇪🇺',
  },
  {
    type: 'POPIA',
    name: 'POPIA Compliance',
    description: 'Protection of Personal Information Act compliance',
    requirements: ['Data protection measures verified', 'Consent management active', 'Data minimization protocols'],
    validity: '12 months',
    icon: '🔒',
  },
  {
    type: 'ISO-27001',
    name: 'ISO 27001 Security',
    description: 'Information security management certification',
    requirements: ['Security audit passed', 'Incident response plan', 'Access controls verified', 'Encryption standards met'],
    validity: '36 months',
    icon: '🛡️',
  },
];

const SAMPLE_CERTIFICATIONS = [
  { agent_id: 'MTP-a3f5b2-7k9m2p', org: 'First National Bank', type: 'ZA-FIN', status: 'CERTIFIED', issued: '2024-01-20', expires: '2025-01-20' },
  { agent_id: 'MTP-a3f5b2-7k9m2p', org: 'First National Bank', type: 'POPIA', status: 'CERTIFIED', issued: '2024-01-22', expires: '2025-01-22' },
  { agent_id: 'MTP-b4c6d3-8l0n3q', org: 'Standard Bank', type: 'ZA-FIN', status: 'CERTIFIED', issued: '2024-02-01', expires: '2025-02-01' },
  { agent_id: 'MTP-b4c6d3-8l0n3q', org: 'Standard Bank', type: 'EU-AI', status: 'PENDING', issued: null, expires: null },
  { agent_id: 'MTP-d6e8f5-0n2p5s', org: 'Nedbank', type: 'ZA-FIN', status: 'EXPIRED', issued: '2023-01-15', expires: '2024-01-15' },
  { agent_id: 'MTP-e7f9g6-1o3q6t', org: 'Absa Group', type: 'ZA-FIN', status: 'CERTIFIED', issued: '2024-01-10', expires: '2025-01-10' },
  { agent_id: 'MTP-e7f9g6-1o3q6t', org: 'Absa Group', type: 'POPIA', status: 'CERTIFIED', issued: '2024-01-12', expires: '2025-01-12' },
  { agent_id: 'MTP-e7f9g6-1o3q6t', org: 'Absa Group', type: 'ISO-27001', status: 'PENDING', issued: null, expires: null },
];

export default function Certifications() {
  const [loading, setLoading] = useState(true);
  const [certifications, setCertifications] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [applyDialogOpen, setApplyDialogOpen] = useState(false);

  useEffect(() => {
    fetchCertifications();
  }, []);

  const fetchCertifications = async () => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setCertifications(SAMPLE_CERTIFICATIONS);
    } catch (error) {
      console.error('Failed to fetch certifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: certifications.length,
    certified: certifications.filter(c => c.status === 'CERTIFIED').length,
    pending: certifications.filter(c => c.status === 'PENDING').length,
    expired: certifications.filter(c => c.status === 'EXPIRED').length,
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'CERTIFIED': return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'PENDING': return <Clock className="h-4 w-4 text-yellow-400" />;
      case 'EXPIRED': return <XCircle className="h-4 w-4 text-red-400" />;
      case 'REJECTED': return <AlertTriangle className="h-4 w-4 text-red-400" />;
      default: return null;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      CERTIFIED: 'bg-green-500/10 text-green-400 border-green-500/20',
      PENDING: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      EXPIRED: 'bg-red-500/10 text-red-400 border-red-500/20',
      REJECTED: 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return variants[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  const getDaysUntilExpiry = (expiryDate) => {
    if (!expiryDate) return null;
    const days = Math.ceil((new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
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
          <h1 className="text-2xl font-bold text-white">Certification Center</h1>
          <p className="text-slate-400">Manage compliance certifications for AI agents</p>
        </div>
        <Button variant="outline" onClick={fetchCertifications} className="border-slate-700 text-slate-400">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Award className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Certifications</p>
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
                <p className="text-sm text-slate-400">Active</p>
                <p className="text-2xl font-bold text-green-400">{stats.certified}</p>
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
                <p className="text-sm text-slate-400">Pending</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.pending}</p>
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
                <p className="text-sm text-slate-400">Expired</p>
                <p className="text-2xl font-bold text-red-400">{stats.expired}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="certifications" className="space-y-6">
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="certifications" className="data-[state=active]:bg-blue-600">Active Certifications</TabsTrigger>
          <TabsTrigger value="available" className="data-[state=active]:bg-blue-600">Available Types</TabsTrigger>
        </TabsList>

        {/* Active Certifications Tab */}
        <TabsContent value="certifications">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Agent Certifications</CardTitle>
              <CardDescription className="text-slate-400">All certifications across registered agents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {certifications.map((cert, index) => {
                  const daysLeft = getDaysUntilExpiry(cert.expires);
                  const isExpiringSoon = daysLeft && daysLeft <= 30 && daysLeft > 0;

                  return (
                    <div
                      key={`${cert.agent_id}-${cert.type}-${index}`}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600/50"
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-2xl">
                          {CERTIFICATION_TYPES.find(t => t.type === cert.type)?.icon || '📜'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white">{cert.type}</span>
                            <Badge variant="outline" className={getStatusBadge(cert.status)}>
                              {getStatusIcon(cert.status)}
                              <span className="ml-1">{cert.status}</span>
                            </Badge>
                            {isExpiringSoon && (
                              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20">
                                Expires in {daysLeft} days
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-sm">
                            <Link to={`/agents/${cert.agent_id}`} className="text-blue-400 hover:text-blue-300 font-mono">
                              {cert.agent_id}
                            </Link>
                            <span className="text-slate-500">-</span>
                            <span className="text-slate-400">{cert.org}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        {cert.status === 'CERTIFIED' && (
                          <>
                            <p className="text-sm text-slate-400">Expires</p>
                            <p className="text-white">{new Date(cert.expires).toLocaleDateString()}</p>
                          </>
                        )}
                        {cert.status === 'PENDING' && (
                          <p className="text-sm text-yellow-400">Review in progress</p>
                        )}
                        {cert.status === 'EXPIRED' && (
                          <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                            Renew
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Available Types Tab */}
        <TabsContent value="available">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {CERTIFICATION_TYPES.map((certType) => (
              <Card key={certType.type} className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl">{certType.icon}</span>
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                      {certType.type}
                    </Badge>
                  </div>
                  <CardTitle className="text-white text-lg">{certType.name}</CardTitle>
                  <CardDescription className="text-slate-400">{certType.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-2">Requirements:</p>
                    <ul className="space-y-1">
                      {certType.requirements.map((req, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-slate-300">
                          <CheckCircle className="h-3 w-3 text-green-400" />
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <Calendar className="h-4 w-4" />
                      Valid for {certType.validity}
                    </div>
                    <Button
                      size="sm"
                      onClick={() => {
                        setSelectedType(certType);
                        setApplyDialogOpen(true);
                      }}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Apply
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Apply Dialog */}
      <Dialog open={applyDialogOpen} onOpenChange={setApplyDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <span className="text-2xl">{selectedType?.icon}</span>
              Apply for {selectedType?.type}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedType?.description}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-400 mb-2">Requirements:</p>
              <ul className="space-y-2">
                {selectedType?.requirements.map((req, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-slate-300">
                    <div className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center">
                      <CheckCircle className="h-3 w-3 text-green-400" />
                    </div>
                    {req}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-sm text-blue-300">
                <Shield className="h-4 w-4 inline mr-2" />
                Certification review typically takes 3-5 business days.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApplyDialogOpen(false)} className="border-slate-700 text-slate-300">
              Cancel
            </Button>
            <Button className="bg-blue-600 hover:bg-blue-700">
              Submit Application
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
