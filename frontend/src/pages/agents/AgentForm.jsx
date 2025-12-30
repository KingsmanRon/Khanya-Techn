/**
 * Agent Registration Form
 * Multi-step wizard for registering new AI agents
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { agentAPI } from '../../services/api';

const STEPS = [
  { id: 1, title: 'Basic Info', description: 'Agent identification' },
  { id: 2, title: 'Capabilities', description: 'Define what the agent can do' },
  { id: 3, title: 'Mandate', description: 'Set operational limits' },
  { id: 4, title: 'Review', description: 'Confirm registration' },
];

const AGENT_TYPES = [
  { value: 'customer_service', label: 'Customer Service' },
  { value: 'fraud_detection', label: 'Fraud Detection' },
  { value: 'trading_bot', label: 'Trading Bot' },
  { value: 'doc_processor', label: 'Document Processor' },
  { value: 'risk_assessment', label: 'Risk Assessment' },
  { value: 'data_analyst', label: 'Data Analyst' },
  { value: 'other', label: 'Other' },
];

const BASE_MODELS = [
  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gemini-pro', label: 'Gemini Pro' },
  { value: 'custom', label: 'Custom Model' },
];

const CAPABILITIES = [
  { id: 'account_inquiry', label: 'Account Inquiry', description: 'View account information' },
  { id: 'balance_check', label: 'Balance Check', description: 'Check account balances' },
  { id: 'transaction_history', label: 'Transaction History', description: 'View past transactions' },
  { id: 'fund_transfer_small', label: 'Small Transfers', description: 'Transfer up to R10,000' },
  { id: 'fund_transfer_large', label: 'Large Transfers', description: 'Transfer over R10,000' },
  { id: 'loan_application', label: 'Loan Applications', description: 'Process loan requests' },
  { id: 'document_verification', label: 'Document Verification', description: 'Verify identity documents' },
  { id: 'fraud_analysis', label: 'Fraud Analysis', description: 'Analyze suspicious activity' },
];

export default function AgentForm() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    // Basic Info
    agent_type: '',
    base_model: '',
    organization: '',
    description: '',

    // Capabilities
    capabilities: [],

    // Mandate
    max_transaction_value: 10000,
    daily_transaction_limit: 100000,
    allowed_operations: ['read'],
    requires_human_approval: false,
    restricted_hours: false,
  });

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleCapability = (capId) => {
    setFormData(prev => ({
      ...prev,
      capabilities: prev.capabilities.includes(capId)
        ? prev.capabilities.filter(c => c !== capId)
        : [...prev.capabilities, capId]
    }));
  };

  const toggleOperation = (op) => {
    setFormData(prev => ({
      ...prev,
      allowed_operations: prev.allowed_operations.includes(op)
        ? prev.allowed_operations.filter(o => o !== op)
        : [...prev.allowed_operations, op]
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.agent_type && formData.base_model && formData.organization;
      case 2:
        return formData.capabilities.length > 0;
      case 3:
        return formData.max_transaction_value > 0 && formData.allowed_operations.length > 0;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await agentAPI.register({
        agent_type: formData.agent_type,
        base_model: formData.base_model,
        organization: formData.organization,
        description: formData.description,
        capabilities: formData.capabilities,
        mandate: {
          max_transaction_value: formData.max_transaction_value,
          daily_transaction_limit: formData.daily_transaction_limit,
          allowed_operations: formData.allowed_operations,
          requires_human_approval: formData.requires_human_approval,
          restricted_hours: formData.restricted_hours,
        },
      });

      // Navigate to the new agent's detail page
      navigate(`/agents/${response.data.mtp_id}`);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to register agent. Please try again.');
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/agents')}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-white">Register New Agent</h1>
          <p className="text-slate-400">Create a new MTP identity for an AI agent</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  currentStep > step.id
                    ? 'bg-green-500 text-white'
                    : currentStep === step.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                {currentStep > step.id ? <Check className="h-4 w-4" /> : step.id}
              </div>
              <div className="hidden sm:block">
                <p className={`text-sm font-medium ${currentStep >= step.id ? 'text-white' : 'text-slate-500'}`}>
                  {step.title}
                </p>
                <p className="text-xs text-slate-500">{step.description}</p>
              </div>
            </div>
            {index < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-4 ${currentStep > step.id ? 'bg-green-500' : 'bg-slate-700'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Form Content */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="pt-6">
          {error && (
            <Alert variant="destructive" className="mb-6 bg-red-500/10 border-red-500/20">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          )}

          {/* Step 1: Basic Info */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label className="text-slate-200">Agent Type *</Label>
                <Select value={formData.agent_type} onValueChange={(v) => updateField('agent_type', v)}>
                  <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
                    <SelectValue placeholder="Select agent type" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {AGENT_TYPES.map(type => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Base Model *</Label>
                <Select value={formData.base_model} onValueChange={(v) => updateField('base_model', v)}>
                  <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
                    <SelectValue placeholder="Select base model" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {BASE_MODELS.map(model => (
                      <SelectItem key={model.value} value={model.value}>{model.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Organization *</Label>
                <Input
                  value={formData.organization}
                  onChange={(e) => updateField('organization', e.target.value)}
                  placeholder="e.g., First National Bank"
                  className="bg-slate-900/50 border-slate-700 text-white"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Description</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  placeholder="Brief description of what this agent does..."
                  className="bg-slate-900/50 border-slate-700 text-white min-h-[100px]"
                />
              </div>
            </div>
          )}

          {/* Step 2: Capabilities */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <p className="text-slate-400 text-sm">Select the capabilities this agent will have:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {CAPABILITIES.map(cap => (
                  <div
                    key={cap.id}
                    onClick={() => toggleCapability(cap.id)}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                      formData.capabilities.includes(cap.id)
                        ? 'bg-blue-600/20 border-blue-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Checkbox
                        checked={formData.capabilities.includes(cap.id)}
                        className="border-slate-500"
                      />
                      <div>
                        <p className="text-white font-medium">{cap.label}</p>
                        <p className="text-slate-400 text-sm">{cap.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Mandate */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label className="text-slate-200">Max Transaction Value (R)</Label>
                  <Input
                    type="number"
                    value={formData.max_transaction_value}
                    onChange={(e) => updateField('max_transaction_value', parseInt(e.target.value))}
                    className="bg-slate-900/50 border-slate-700 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">Daily Transaction Limit (R)</Label>
                  <Input
                    type="number"
                    value={formData.daily_transaction_limit}
                    onChange={(e) => updateField('daily_transaction_limit', parseInt(e.target.value))}
                    className="bg-slate-900/50 border-slate-700 text-white"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Allowed Operations</Label>
                <div className="flex flex-wrap gap-2">
                  {['read', 'write', 'transfer', 'approve', 'delete'].map(op => (
                    <Button
                      key={op}
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => toggleOperation(op)}
                      className={formData.allowed_operations.includes(op)
                        ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                        : 'border-slate-600 text-slate-400'
                      }
                    >
                      {op}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-slate-700">
                <div className="flex items-center gap-3">
                  <Checkbox
                    checked={formData.requires_human_approval}
                    onCheckedChange={(v) => updateField('requires_human_approval', v)}
                  />
                  <div>
                    <p className="text-white">Require Human Approval</p>
                    <p className="text-slate-400 text-sm">Large transactions require manual approval</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Checkbox
                    checked={formData.restricted_hours}
                    onCheckedChange={(v) => updateField('restricted_hours', v)}
                  />
                  <div>
                    <p className="text-white">Restrict to Business Hours</p>
                    <p className="text-slate-400 text-sm">Only operate during 08:00 - 17:00 SAST</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="p-4 bg-slate-700/30 rounded-lg space-y-3">
                <h3 className="text-white font-medium">Basic Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-slate-400">Type:</span>
                  <span className="text-white">{formData.agent_type}</span>
                  <span className="text-slate-400">Model:</span>
                  <span className="text-white">{formData.base_model}</span>
                  <span className="text-slate-400">Organization:</span>
                  <span className="text-white">{formData.organization}</span>
                </div>
              </div>

              <div className="p-4 bg-slate-700/30 rounded-lg space-y-3">
                <h3 className="text-white font-medium">Capabilities</h3>
                <div className="flex flex-wrap gap-2">
                  {formData.capabilities.map(cap => (
                    <span key={cap} className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-sm">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-slate-700/30 rounded-lg space-y-3">
                <h3 className="text-white font-medium">Mandate</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-slate-400">Max Transaction:</span>
                  <span className="text-white">R{formData.max_transaction_value.toLocaleString()}</span>
                  <span className="text-slate-400">Daily Limit:</span>
                  <span className="text-white">R{formData.daily_transaction_limit.toLocaleString()}</span>
                  <span className="text-slate-400">Operations:</span>
                  <span className="text-white">{formData.allowed_operations.join(', ')}</span>
                </div>
              </div>

              <Alert className="bg-blue-500/10 border-blue-500/20">
                <Shield className="h-4 w-4 text-blue-400" />
                <AlertDescription className="text-blue-300">
                  A unique MTP ID and Ed25519 keypair will be generated for this agent.
                  The private key will be provided once and cannot be recovered.
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-slate-700">
            <Button
              variant="outline"
              onClick={() => setCurrentStep(s => s - 1)}
              disabled={currentStep === 1}
              className="border-slate-700 text-slate-300"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            {currentStep < 4 ? (
              <Button
                onClick={() => setCurrentStep(s => s + 1)}
                disabled={!canProceed()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Registering...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Register Agent
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
