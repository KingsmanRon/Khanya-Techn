/**
 * MTP API Service Layer
 * Centralized API client with authentication and error handling
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('mtp_token');
    const apiKey = localStorage.getItem('mtp_api_key');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (apiKey) {
      config.headers['X-MTP-API-Key'] = apiKey;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('mtp_token');
      localStorage.removeItem('mtp_api_key');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// Health & System
// ============================================
export const healthAPI = {
  check: () => apiClient.get('/api/health'),
  getSystemStatus: () => apiClient.get('/api/v1/system/status'),
};

// ============================================
// Authentication & API Keys
// ============================================
export const authAPI = {
  login: (credentials) => apiClient.post('/api/v1/auth/login', credentials),
  logout: () => apiClient.post('/api/v1/auth/logout'),
  getApiKeys: () => apiClient.get('/api/v1/api-keys'),
  createApiKey: (data) => apiClient.post('/api/v1/api-keys', data),
  revokeApiKey: (keyId) => apiClient.delete(`/api/v1/api-keys/${keyId}`),
};

// ============================================
// Agent Management (MTP-ID)
// ============================================
export const agentAPI = {
  // List all agents with optional filters
  list: (params = {}) => apiClient.get('/api/v1/agents', { params }),

  // Get single agent by MTP ID
  get: (mtpId) => apiClient.get(`/api/v1/agents/${mtpId}`),

  // Register new agent
  register: (agentData) => apiClient.post('/api/v1/identity/register', agentData),

  // Update agent
  update: (mtpId, data) => apiClient.patch(`/api/v1/agents/${mtpId}`, data),

  // Suspend agent
  suspend: (mtpId, reason) => apiClient.post(`/api/v1/agents/${mtpId}/suspend`, { reason }),

  // Reactivate agent
  activate: (mtpId) => apiClient.post(`/api/v1/agents/${mtpId}/activate`),

  // Revoke agent keys
  revokeKeys: (mtpId) => apiClient.post(`/api/v1/agents/${mtpId}/revoke-keys`),

  // Get agent activity
  getActivity: (mtpId, params = {}) => apiClient.get(`/api/v1/agents/${mtpId}/activity`, { params }),
};

// ============================================
// Audit Trail (MTP-AUDIT)
// ============================================
export const auditAPI = {
  // List audit events with filters
  list: (params = {}) => apiClient.get('/api/v1/audit/events', { params }),

  // Get single event
  get: (eventId) => apiClient.get(`/api/v1/audit/events/${eventId}`),

  // Get events for specific agent
  getByAgent: (mtpId, params = {}) => apiClient.get(`/api/v1/audit/agents/${mtpId}/events`, { params }),

  // Get event statistics
  getStats: (params = {}) => apiClient.get('/api/v1/audit/stats', { params }),

  // Log new event (for testing)
  logEvent: (eventData) => apiClient.post('/api/v1/audit/events', eventData),
};

// ============================================
// Trust Score (MTP-TRUST)
// ============================================
export const trustAPI = {
  // Get trust score for agent
  getScore: (mtpId) => apiClient.get(`/api/v1/trust/${mtpId}`),

  // Get trust score history
  getHistory: (mtpId, params = {}) => apiClient.get(`/api/v1/trust/${mtpId}/history`, { params }),

  // Get trust score breakdown
  getBreakdown: (mtpId) => apiClient.get(`/api/v1/trust/${mtpId}/breakdown`),

  // Get all agents' trust scores
  getAllScores: (params = {}) => apiClient.get('/api/v1/trust', { params }),

  // Get trust score distribution
  getDistribution: () => apiClient.get('/api/v1/trust/distribution'),
};

// ============================================
// Certifications (MTP-CERT)
// ============================================
export const certificationAPI = {
  // List all certifications for an agent
  list: (mtpId) => apiClient.get(`/api/v1/certifications/${mtpId}`),

  // Get available certification types
  getTypes: () => apiClient.get('/api/v1/certifications/types'),

  // Apply for certification
  apply: (mtpId, certType) => apiClient.post(`/api/v1/certifications/${mtpId}/apply`, { certification_type: certType }),

  // Check certification requirements
  checkRequirements: (mtpId, certType) => apiClient.get(`/api/v1/certifications/${mtpId}/requirements/${certType}`),

  // Renew certification
  renew: (mtpId, certType) => apiClient.post(`/api/v1/certifications/${mtpId}/renew`, { certification_type: certType }),
};

// ============================================
// Insurance & Risk (MTP-INSURE)
// ============================================
export const insuranceAPI = {
  // Get risk profile for agent
  getRiskProfile: (mtpId) => apiClient.get(`/api/v1/insurance/${mtpId}/risk`),

  // Calculate premium
  calculatePremium: (mtpId, coverage) => apiClient.post(`/api/v1/insurance/${mtpId}/premium`, coverage),

  // Get coverage recommendations
  getRecommendations: (mtpId) => apiClient.get(`/api/v1/insurance/${mtpId}/recommendations`),

  // List all risk profiles
  listProfiles: (params = {}) => apiClient.get('/api/v1/insurance/profiles', { params }),
};

// ============================================
// Disputes (MTP-RESOLVE)
// ============================================
export const disputeAPI = {
  // List disputes
  list: (params = {}) => apiClient.get('/api/v1/disputes', { params }),

  // Get single dispute
  get: (disputeId) => apiClient.get(`/api/v1/disputes/${disputeId}`),

  // File new dispute
  create: (disputeData) => apiClient.post('/api/v1/disputes', disputeData),

  // Add evidence to dispute
  addEvidence: (disputeId, evidence) => apiClient.post(`/api/v1/disputes/${disputeId}/evidence`, evidence),

  // Update dispute status
  updateStatus: (disputeId, status) => apiClient.patch(`/api/v1/disputes/${disputeId}/status`, { status }),

  // Get dispute statistics
  getStats: () => apiClient.get('/api/v1/disputes/stats'),
};

// ============================================
// Blockchain (MTP-CHAIN)
// ============================================
export const blockchainAPI = {
  // Get latest batch info
  getLatestBatch: () => apiClient.get('/api/v1/blockchain/batches/latest'),

  // List all batches
  listBatches: (params = {}) => apiClient.get('/api/v1/blockchain/batches', { params }),

  // Get specific batch
  getBatch: (batchId) => apiClient.get(`/api/v1/blockchain/batches/${batchId}`),

  // Verify merkle proof
  verifyProof: (eventId) => apiClient.get(`/api/v1/blockchain/verify/${eventId}`),

  // Get pending events count
  getPendingCount: () => apiClient.get('/api/v1/blockchain/pending'),

  // Get anchoring status
  getAnchoringStatus: () => apiClient.get('/api/v1/blockchain/status'),
};

// ============================================
// Gateway (Kill Switch)
// ============================================
export const gatewayAPI = {
  // Verify request
  verify: (request) => apiClient.post('/api/v1/gateway/verify', request),

  // Get gateway stats
  getStats: () => apiClient.get('/api/v1/gateway/stats'),
};

// ============================================
// Dashboard Aggregates
// ============================================
export const dashboardAPI = {
  // Get overview stats
  getOverview: async () => {
    try {
      const [health, agents, audits] = await Promise.all([
        healthAPI.check().catch(() => ({ data: { status: 'unknown' } })),
        agentAPI.list({ limit: 100 }).catch(() => ({ data: [] })),
        auditAPI.getStats().catch(() => ({ data: {} })),
      ]);

      return {
        systemStatus: health.data,
        agents: agents.data,
        auditStats: audits.data,
      };
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      throw error;
    }
  },
};

export default apiClient;
