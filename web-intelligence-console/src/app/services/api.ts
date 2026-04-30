// F.A.R.O. Web Intelligence Console - API Service
import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  AnalystConclusion,
  AnalystDecision,
  AnalystFeedbackEvent,
  AnalystFeedbackTemplate,
  DashboardStats,
  FeedbackForAgent,
  IntelligenceQueueItem,
  WatchlistCategory,
  WatchlistEntry,
  WatchlistStatus,
  IntelligenceCase,
  AuditLogEntry,
  PaginatedResponse,
  PaginationParams,
  SuspicionLevel,
  UrgencyLevel,
  SuspicionReason,
  ReviewStatus,
  ApiError,
  Agency,
  Alert,
  AlertRule,
  RoutePattern,
  ObservationDetail,
  Device,
  AgentLocationEntry,
  GeolocationAuditFilter,
  AgentMovementAnalysisResult,
  CoverageMapCell,
  AgentObservationCorrelation,
  TacticalPositioningRecommendation,
  User,
  UserFormData,
  VehicleObservation,
  AnalystReview,
  AnalystReviewStatus,
  FeedbackRecipient,
  AlgorithmResult,
} from '@/app/types';
import logger from '@/app/utils/logger';

// ============================================================================
// HTTP Cache (Simple in-memory cache)
// ============================================================================
interface CacheEntry {
  data: unknown;
  timestamp: number;
}

const httpCache = new Map<string, CacheEntry>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes default
const MAX_CACHE_SIZE = 100;

function getCachedData(key: string): unknown | null {
  const entry = httpCache.get(key);
  if (!entry) return null;
  
  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    httpCache.delete(key);
    return null;
  }
  
  return entry.data;
}

function setCachedData(key: string, data: unknown): void {
  // Evict oldest if cache is full
  if (httpCache.size >= MAX_CACHE_SIZE) {
    const oldestKey = httpCache.keys().next().value;
    if (oldestKey) {
      httpCache.delete(oldestKey);
    }
  }
  httpCache.set(key, { data, timestamp: Date.now() });
}

function generateCacheKey(config: InternalAxiosRequestConfig): string {
  return `${config.method}:${config.url}:${JSON.stringify(config.params || {})}`;
}

// ============================================================================
// Circuit Breaker State
// ============================================================================
type CircuitState = 'closed' | 'open' | 'half_open';

interface CircuitBreakerState {
  state: CircuitState;
  failures: number;
  lastFailureTime: number;
  successes: number;
}

const circuitBreakers: Map<string, CircuitBreakerState> = new Map();

// Config
const CIRCUIT_FAILURE_THRESHOLD = 5;
const CIRCUIT_SUCCESS_THRESHOLD = 2;
const CIRCUIT_TIMEOUT_MS = 30000; // 30s timeout for better UX

function getCircuitBreaker(name: string): CircuitBreakerState {
  if (!circuitBreakers.has(name)) {
    circuitBreakers.set(name, { state: 'closed', failures: 0, lastFailureTime: 0, successes: 0 });
  }
  return circuitBreakers.get(name)!;
}

function recordCircuitSuccess(name: string): void {
  const cb = getCircuitBreaker(name);
  cb.failures = 0;
  cb.successes++;
  if (cb.state === 'half_open' && cb.successes >= CIRCUIT_SUCCESS_THRESHOLD) {
    cb.state = 'closed';
    cb.successes = 0;
  }
}

function recordCircuitFailure(name: string): void {
  const cb = getCircuitBreaker(name);
  cb.failures++;
  cb.lastFailureTime = Date.now();
  cb.successes = 0;
  if (cb.state === 'closed' && cb.failures >= CIRCUIT_FAILURE_THRESHOLD) {
    cb.state = 'open';
  } else if (cb.state === 'half_open') {
    cb.state = 'open';
  }
}

function canExecute(name: string): boolean {
  const cb = getCircuitBreaker(name);
  if (cb.state === 'closed') return true;
  if (cb.state === 'open') {
    if (Date.now() - cb.lastFailureTime > CIRCUIT_TIMEOUT_MS) {
      cb.state = 'half_open';
      cb.successes = 0;
      return true;
    }
    return false;
  }
  return true;
}

// ============================================================================
// Retry Interceptor with Exponential Backoff
// ============================================================================
const RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504];
const RETRY_MAX_ATTEMPTS = 3;
const RETRY_BASE_DELAY_MS = 1000;

function shouldRetryResponse(status: number): boolean {
  return RETRY_STATUS_CODES.includes(status);
}

function calculateRetryDelay(attempt: number): number {
  // Exponential backoff: 1s, 2s, 4s
  return RETRY_BASE_DELAY_MS * Math.pow(2, attempt - 1);
}

// ============================================================================
// Offline Detection
// ============================================================================
let isOnlineStatus = true;
let lastOnlineCheck = 0;

function checkOnline(): boolean {
  // Debounce check to avoid excessive calls
  const now = Date.now();
  if (now - lastOnlineCheck < 1000) return isOnlineStatus;
  
  lastOnlineCheck = now;
  isOnlineStatus = typeof navigator !== 'undefined' ? navigator.onLine : true;
  return isOnlineStatus;
}

// ============================================================================
// Create axios instance
// ============================================================================
const api: AxiosInstance = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Auth + Cache + Cache Busting
api.interceptors.request.use(
  (config) => {
    // Auth token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Cache busting for critical endpoints (always fresh data)
    const criticalEndpoints = ['/intelligence/queue', '/intelligence/observations/', '/intelligence/reviews'];
    const isCritical = criticalEndpoints.some(endpoint => config.url?.includes(endpoint));
    
    if (isCritical) {
      // Add timestamp to bypass cache for critical data
      config.params = { ...config.params, _t: Date.now() };
    } else {
      // Check for cached response (GET only, non-critical)
      if (config.method === 'get') {
        const cacheKey = generateCacheKey(config);
        const cached = getCachedData(cacheKey);
        if (cached) {
          // Return cached response wrapped in promise
          return Promise.resolve(cached as AxiosResponse).then(response => {
            // Mark as from cache
            (response as AxiosResponse & { fromCache: boolean }).fromCache = true;
            return config;
          });
        }
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Cache + Circuit + Errors
api.interceptors.response.use(
  (response: AxiosResponse & { config?: InternalAxiosRequestConfig }) => {
    recordCircuitSuccess('network');
    
    // Cache GET responses
    if (response.config?.method === 'get') {
      const cacheKey = generateCacheKey(response.config);
      setCachedData(cacheKey, response);
    }
    
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Safety check: ensure error is an object
    if (!error || typeof error !== 'object') {
      logger.error('API Error: Invalid error object');
      return Promise.reject(error);
    }

    const status = error.response?.status;
    const url = error.config?.url;
    const code = error.code;
    const message = error.message;

    // Use logger.apiError for consistent API error handling
    logger.apiError(url, status, code, message);

    recordCircuitFailure('network');

    if (status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }

    if (error.response) {
      const errorData = error.response?.data as any || {};
      const apiError: ApiError = {
        connection_error: getConnectionErrorMessage(error),
        ...errorData,
      };
    } else {
      const apiError: ApiError = {
        error: 'Connection Error',
        message: getConnectionErrorMessage(error),
        timestamp: new Date().toISOString()
      };
      error.response = apiError as any;
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// Connection Error Messages
// ============================================================================
function getConnectionErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError;
  if (!axiosError.response) {
    const code = axiosError.code;
    if (code === 'ECONNABORTED' || code === 'ETIMEDOUT') {
      return 'Tempo limite excedido. Verifique sua conexão.';
    }
    if (code === 'ECONNREFUSED' || code === 'ENOTFOUND' || code === 'ENETUNREACH') {
      if (!checkOnline()) {
        return 'Você está offline. Conecte-se à internet para continuar.';
      }
      return 'Servidor indisponível. Tente novamente mais tarde.';
    }
    return 'Erro de conexão. Verifique sua internet.';
  }
  const status = axiosError.response.status;
  if (status === 500) return 'Erro interno do servidor.';
  if (status === 502 || status === 503) return 'Serviço temporariamente indisponível.';
  if (status === 504) return 'Tempo limite excedido.';
  const errorDetail = (axiosError.response?.data as any)?.detail || axiosError.message || 'Unknown error';
  return errorDetail;
}

// ============================================================================
// Export utilities for external use
// ============================================================================
export { 
  // Utilities
  checkOnline as isOnline, 
  canExecute, 
  getCircuitBreaker, 
  getConnectionErrorMessage,
  // Cache
  httpCache,
  getCachedData,
  setCachedData,
};

// ============================================================================
// Asset URL Helper
// ============================================================================
/**
 * Generate asset URL from bucket and key
 * @param bucket - Storage bucket name (e.g., "faro-assets" or "local")
 * @param key - File key/path (e.g., "observations/123/image/abc.jpg")
 * @returns Full URL to access the asset
 */
export function getAssetUrl(bucket: string, key: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return `${baseUrl}/api/v1/assets/${bucket}/${key}`;
}

/**
 * Generate plate image URL from PlateRead
 * @param plateRead - PlateRead object with bucket and key
 * @returns Full URL to the plate image or undefined if no image
 */
export function getPlateImageUrl(plateRead: { image_url?: string }): string | undefined {
  if (!plateRead.image_url) return undefined;
  
  // If image_url is already a full URL, return as-is
  if (plateRead.image_url.startsWith('http://') || plateRead.image_url.startsWith('https://')) {
    return plateRead.image_url;
  }
  
  // Otherwise, assume it's a key and construct URL
  // Default to faro-assets bucket if not specified
  const bucket = 'faro-assets';
  return getAssetUrl(bucket, plateRead.image_url);
}

/**
 * Generate evidence URLs from SuspicionReport
 * @param report - SuspicionReport object with image_url and audio_url
 * @returns Array of evidence items with URLs and types
 */
export function getEvidenceUrls(report: { image_url?: string; audio_url?: string }): Array<{ url: string; type: 'image' | 'audio' | 'video'; filename?: string }> {
  const items: Array<{ url: string; type: 'image' | 'audio' | 'video'; filename?: string }> = [];
  
  if (report.image_url) {
    const url = report.image_url.startsWith('http') ? report.image_url : getAssetUrl('faro-assets', report.image_url);
    items.push({ url, type: 'image', filename: 'evidence.jpg' });
  }
  
  if (report.audio_url) {
    const url = report.audio_url.startsWith('http') ? report.audio_url : getAssetUrl('faro-assets', report.audio_url);
    items.push({ url, type: 'audio', filename: 'evidence.mp3' });
  }
  
  return items;
}

// User Management API
export const userApi = {
  listUsers: async (params?: { role?: string; agency_id?: string; page?: number; page_size?: number }) => {
    const response = await api.get('/auth/users', { params });
    return response.data;
  },

  createUser: async (userData: UserFormData) => {
    const response = await api.post('/auth/users', userData);
    return response.data;
  },

  updateUser: async (userId: string, userData: Partial<UserFormData>) => {
    const response = await api.put(`/auth/users/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId: string) => {
    await api.delete(`/auth/users/${userId}`);
  },

  toggleUserActive: async (userId: string): Promise<User> => {
    const response = await api.patch(`/auth/users/${userId}/toggle-active`);
    return response.data;
  },

  verifyUser: async (userId: string): Promise<User> => {
    const response = await api.patch(`/auth/users/${userId}/verify`);
    return response.data;
  },
};

// Auth API
export const authApi = {
  login: async (identifier: string, password: string, deviceInfo?: {
    device_id?: string;
    device_model?: string;
    os_version?: string;
    app_version?: string;
  }) => {
    const response = await api.post('/auth/login', {
      identifier,  // Can be CPF (11 digits) or email
      password,
      ...deviceInfo,
    });
    return response.data;
  },

  refreshToken: async (refreshToken: string) => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  logout: async () => {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    await api.post('/auth/password/change', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  listUsers: userApi.listUsers,
  createUser: userApi.createUser,
  updateUser: userApi.updateUser,
  deleteUser: userApi.deleteUser,
  toggleUserActive: userApi.toggleUserActive,
  verifyUser: userApi.verifyUser,
};

// Mobile/Observations API (for history)
export const mobileApi = {
  getHistory: async (params?: PaginationParams): Promise<PaginatedResponse<VehicleObservation>> => {
    const response = await api.get('/mobile/history', { params });
    return response.data;
  },

  getObservation: async (id: string): Promise<VehicleObservation> => {
    const response = await api.get(`/mobile/observations/${id}`);
    return response.data;
  },

  getObservationFeedback: async (id: string) => {
    const response = await api.get(`/mobile/observations/${id}/feedback`);
    return response.data;
  },
};

// Intelligence API
export const intelligenceApi = {
  getQueue: async (filters?: {
    plate_number?: string;
    suspicion_level?: SuspicionLevel;
    urgency?: UrgencyLevel;
    reason?: SuspicionReason;
    agent_id?: string;
    unit_id?: string;
    status?: ReviewStatus;
    date_from?: string;
    date_to?: string;
  }, pagination?: PaginationParams): Promise<IntelligenceQueueItem[]> => {
    const response = await api.get('/intelligence/queue', { 
      params: { ...filters, ...pagination } 
    });
    return response.data;
  },

  createReview: async (data: {
    observation_id: string;
    status: AnalystReviewStatus;
    conclusion?: AnalystConclusion;
    decision?: AnalystDecision;
    source_quality?: string;
    data_reliability?: string;
    reinforcing_factors?: Record<string, unknown>;
    weakening_factors?: Record<string, unknown>;
    recommendation?: string;
    justification: string;
    sensitivity_level?: string;
    review_due_at?: string;
    linked_case_id?: string;
    linked_occurrence_ref?: string;
    change_reason?: string;
  }): Promise<AnalystReview> => {
    const response = await api.post('/intelligence/reviews', data);
    return response.data;
  },

  updateReview: async (id: string, data: {
    status?: AnalystReviewStatus;
    conclusion?: AnalystConclusion;
    decision?: AnalystDecision;
    source_quality?: string;
    data_reliability?: string;
    reinforcing_factors?: Record<string, unknown>;
    weakening_factors?: Record<string, unknown>;
    recommendation?: string;
    justification?: string;
    sensitivity_level?: string;
    review_due_at?: string;
    linked_case_id?: string;
    linked_occurrence_ref?: string;
    change_reason?: string;
  }): Promise<AnalystReview> => {
    const response = await api.patch(`/intelligence/reviews/${id}`, data);
    return response.data;
  },

  getPendingFeedback: async (): Promise<FeedbackForAgent[]> => {
    const response = await api.get('/intelligence/feedback/pending');
    return response.data;
  },

  createFeedback: async (data: {
    observation_id?: string;
    target_user_id?: string;
    target_team_label?: string;
    feedback_type: string;
    sensitivity_level?: string;
    title: string;
    message?: string;
    template_id?: string;
  }): Promise<AnalystFeedbackEvent> => {
    const response = await api.post('/intelligence/feedback', data);
    return response.data;
  },

  listFeedbackTemplates: async (active_only: boolean = true): Promise<AnalystFeedbackTemplate[]> => {
    const response = await api.get('/intelligence/feedback/templates', {
      params: { active_only },
    });
    return response.data;
  },

  listFeedbackRecipients: async (params?: {
    query?: string;
    limit?: number;
  }): Promise<FeedbackRecipient[]> => {
    const response = await api.get('/intelligence/feedback/recipients', { params });
    return response.data;
  },

  createFeedbackTemplate: async (data: {
    name: string;
    feedback_type: string;
    sensitivity_level?: string;
    body_template: string;
    is_active?: boolean;
  }): Promise<AnalystFeedbackTemplate> => {
    const response = await api.post('/intelligence/feedback/templates', data);
    return response.data;
  },

  markFeedbackRead: async (feedbackId: string) => {
    await api.post(`/intelligence/feedback/${feedbackId}/read`, {
      read_at: new Date().toISOString(),
    });
  },

  listWatchlist: async (status?: WatchlistStatus): Promise<WatchlistEntry[]> => {
    const response = await api.get('/intelligence/watchlists', {
      params: status ? { status } : undefined,
    });
    return response.data;
  },

  createWatchlistEntry: async (data: {
    status?: WatchlistStatus;
    category: WatchlistCategory;
    plate_number?: string;
    plate_partial?: string;
    vehicle_make?: string;
    vehicle_model?: string;
    vehicle_color?: string;
    visual_traits?: string;
    interest_reason: string;
    information_source?: string;
    sensitivity_level?: string;
    confidence_level?: string;
    geographic_scope?: string;
    active_time_window?: string;
    priority?: number;
    recommended_action?: string;
    silent_mode?: boolean;
    notes?: string;
    valid_from?: string;
    valid_until?: string;
    review_due_at?: string;
    metadata_json?: Record<string, unknown>;
  }): Promise<WatchlistEntry> => {
    const response = await api.post('/intelligence/watchlists', data);
    return response.data;
  },

  updateWatchlistEntry: async (id: string, data: Partial<WatchlistEntry>): Promise<WatchlistEntry> => {
    const response = await api.patch(`/intelligence/watchlists/${id}`, data);
    return response.data;
  },

  deleteWatchlistEntry: async (id: string): Promise<{ message: string }> => {
    const response = await api.delete(`/intelligence/watchlists/${id}`);
    return response.data;
  },

  getObservationDetail: async (id: string): Promise<ObservationDetail> => {
    const response = await api.get(`/intelligence/observations/${id}`);
    return response.data;
  },

  listRoutes: async (plate_number?: string): Promise<AlgorithmResult[]> => {
    const response = await api.get('/intelligence/routes', { params: plate_number ? { plate_number } : undefined });
    return response.data;
  },

  listConvoys: async (plate_number?: string): Promise<AlgorithmResult[]> => {
    const response = await api.get('/intelligence/convoys', { params: plate_number ? { plate_number } : undefined });
    return response.data;
  },

  listRoaming: async (plate_number?: string): Promise<AlgorithmResult[]> => {
    const response = await api.get('/intelligence/roaming', { params: plate_number ? { plate_number } : undefined });
    return response.data;
  },

  listSensitiveAssets: async (params?: { plate_number?: string; zone_id?: string }): Promise<AlgorithmResult[]> => {
    const response = await api.get('/intelligence/sensitive-assets', { params });
    return response.data;
  },

  createCase: async (data: {
    title: string;
    hypothesis?: string;
    summary?: string;
    status?: IntelligenceCase['status'];
    sensitivity_level?: string;
    priority?: number;
    review_due_at?: string;
  }): Promise<IntelligenceCase> => {
    const response = await api.post('/intelligence/cases', data);
    return response.data;
  },

  listCases: async (params?: {
    status?: IntelligenceCase['status'];
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<IntelligenceCase[]> => {
    const response = await api.get('/intelligence/cases', { params });
    return response.data;
  },

  updateCase: async (id: string, data: Partial<IntelligenceCase>): Promise<IntelligenceCase> => {
    const response = await api.patch(`/intelligence/cases/${id}`, data);
    return response.data;
  },

  deleteCase: async (id: string): Promise<{ message: string }> => {
    const response = await api.delete(`/intelligence/cases/${id}`);
    return response.data;
  },

  listCaseLinks: async (caseId: string, linkType?: string): Promise<any[]> => {
    const response = await api.get(`/intelligence/cases/${caseId}/links`, {
      params: linkType ? { link_type: linkType } : undefined,
    });
    return response.data;
  },

  addCaseLink: async (caseId: string, data: {
    link_type: string;
    linked_entity_id: string;
    linked_label?: string;
  }): Promise<any> => {
    const response = await api.post(`/intelligence/cases/${caseId}/links`, data);
    return response.data;
  },

  removeCaseLink: async (caseId: string, linkId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/intelligence/cases/${caseId}/links/${linkId}`);
    return response.data;
  },

  listAuditLogs: async (params?: {
    action?: string;
    resource_type?: string;
    resource_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<AuditLogEntry[]> => {
    const response = await api.get('/audit/logs', { params });
    return response.data;
  },
  
  getAgentGeotrail: async (filters: GeolocationAuditFilter): Promise<AgentLocationEntry[]> => {
    const response = await api.get('/audit/geolocation', { params: filters });
    return response.data;
  },

  exportGeotrail: async (filters: GeolocationAuditFilter, format: 'pdf' | 'docx' | 'xlsx'): Promise<Blob> => {
    const response = await api.get(`/audit/geolocation/export/${format}`, {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  },

  // Agent Movement Analysis
  analyzeAgentMovement: async (payload: {
    agent_id?: string;
    start_date?: string;
    end_date?: string;
    cluster_radius_meters?: number;
    min_points_per_cluster?: number;
  }): Promise<AgentMovementAnalysisResult> => {
    const response = await api.post('/audit/agent-movement/analyze', payload);
    return response.data;
  },

  getAgentCoverageMap: async (payload: {
    start_date?: string;
    end_date?: string;
    grid_size_meters?: number;
  }): Promise<CoverageMapCell[]> => {
    const response = await api.post('/audit/agent-movement/coverage-map', payload);
    return response.data;
  },

  analyzeAgentObservationCorrelation: async (payload: {
    agent_id?: string;
    start_date?: string;
    end_date?: string;
    proximity_radius_meters?: number;
  }): Promise<AgentObservationCorrelation[]> => {
    const response = await api.post('/audit/agent-movement/correlation', payload);
    return response.data;
  },

  getTacticalPositioningRecommendations: async (payload: {
    start_date?: string;
    end_date?: string;
  }): Promise<TacticalPositioningRecommendation[]> => {
    const response = await api.post('/audit/agent-movement/tactical-positioning', payload);
    return response.data;
  },
};

// Alerts API
export const alertsApi = {
  getAlerts: async (filters?: {
    alert_type?: string;
    severity?: string;
    is_acknowledged?: boolean;
    start_date?: string;
    end_date?: string;
    plate_number?: string;
  }, pagination?: PaginationParams): Promise<PaginatedResponse<Alert>> => {
    // Convert getAlerts to use getAggregatedAlerts
    const response = await api.post('/intelligence/alerts/aggregated', {
      limit: pagination?.limit || 100,
      alert_type: filters?.alert_type,
      severity: filters?.severity,
    });
    return {
      items: response.data.items || [],
      total: response.data.total || 0,
      total_count: response.data.total_count || response.data.total || 0,
      page: response.data.page || 1,
      size: response.data.size || 20,
      pages: response.data.pages || 0,
      has_next: response.data.has_next || false,
      has_prev: response.data.has_prev || false,
    };
  },

  acknowledgeAlert: async (id: string) => {
    await api.post(`/alerts/${id}/acknowledge`);
  },

  getAlertRules: async (): Promise<AlertRule[]> => {
    const response = await api.get('/alerts/rules');
    return response.data;
  },

  createAlertRule: async (data: Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>): Promise<AlertRule> => {
    const response = await api.post('/alerts/rules', data);
    return response.data;
  },

  updateAlertRule: async (id: string, data: Partial<AlertRule>): Promise<AlertRule> => {
    const response = await api.patch(`/alerts/rules/${id}`, data);
    return response.data;
  },

  deleteAlertRule: async (id: string): Promise<{ message: string }> => {
    const response = await api.delete(`/alerts/rules/${id}`);
    return response.data;
  },

  getAlertStats: async () => {
    const response = await api.get('/alerts/stats');
    return response.data;
  },

  getAggregatedAlerts: async (filters?: {
    alert_type?: string;
    severity?: string;
    limit?: number;
  }): Promise<{
    total_alerts: number;
    alerts: Array<{
      alert_type: string;
      plate_number: string;
      severity: string;
      confidence: number;
      details: Record<string, unknown>;
      triggered_at: string;
      requires_review: boolean;
    }>;
    summary: Record<string, unknown>;
  }> => {
    const response = await api.post('/intelligence/alerts/aggregated', {
      limit: 100,
      ...filters,
    });
    return response.data;
  },
};

// Hotspots API
export const hotspotsApi = {
  analyze: async (payload?: {
    start_date?: string;
    end_date?: string;
    cluster_radius_meters?: number;
    min_points_per_cluster?: number;
  }): Promise<{
    hotspots: Array<{
      latitude: number;
      longitude: number;
      observation_count: number;
      suspicion_count: number;
      unique_plates: number;
      radius_meters: number;
      intensity_score: number;
    }>;
    total_observations: number;
    total_suspicions: number;
    analysis_period_days: number;
    cluster_radius_meters: number;
    min_points_per_cluster: number;
  }> => {
    const response = await api.post('/intelligence/hotspots/analyze', {
      cluster_radius_meters: 500,
      min_points_per_cluster: 5,
      ...payload,
    });
    return response.data;
  },
};

// Suspicious Routes API
export const suspiciousRoutesApi = {
  list: async (filters?: {
    crime_type?: string;
    risk_level?: string;
    approval_status?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{
    routes: Array<{
      id: string;
      name: string;
      crime_type: string;
      risk_level: string;
      route_points: Array<{ latitude: number; longitude: number }>;
      direction: string;
      is_active: boolean;
      approval_status: string;
      justification?: string;
    }>;
    total_count: number;
    page: number;
    page_size: number;
  }> => {
    const response = await api.get('/intelligence/suspicious-routes', { params: filters });
    return response.data;
  },

  create: async (payload: {
    name: string;
    crime_type: string;
    direction: string;
    risk_level: string;
    route_points: Array<{ latitude: number; longitude: number }>;
    justification?: string;
  }) => {
    const response = await api.post('/intelligence/suspicious-routes', payload);
    return response.data;
  },

  approve: async (routeId: string, payload: { approval_status: 'approved' | 'rejected'; justification?: string }) => {
    const response = await api.post(`/intelligence/suspicious-routes/${routeId}/approve`, payload);
    return response.data;
  },

  remove: async (routeId: string) => {
    const response = await api.delete(`/intelligence/suspicious-routes/${routeId}`);
    return response.data;
  },
};

// Routes API
export const routesApi = {
  getRoutePattern: async (plateNumber: string): Promise<RoutePattern> => {
    const response = await api.get(`/intelligence/routes/${plateNumber}`);
    return response.data;
  },

  analyzeRoute: async (plateNumber: string, params?: {
    start_date?: string;
    end_date?: string;
    min_observations?: number;
  }): Promise<RoutePattern> => {
    const response = await api.post('/intelligence/routes/analyze', {
      plate_number: plateNumber,
      ...params,
    });
    return response.data;
  },

  getTimeline: async (plateNumber: string): Promise<{
    plate_number: string;
    total_observations: number;
    time_span_hours: number;
    items: Array<{
      observation_id: string;
      timestamp: string;
      location: { latitude: number; longitude: number };
      agent_name: string;
      unit_name?: string;
      has_suspicion: boolean;
    }>;
  }> => {
    const response = await api.get(`/intelligence/routes/${plateNumber}/timeline`);
    return response.data;
  },

  // Route Prediction
  predict: async (plateNumber: string, daysAhead?: number): Promise<{
    plate_number: string;
    predicted_corridor: Array<[number, number]>;
    confidence: number;
    predicted_hours: number[];
    predicted_days: number[];
    last_pattern_analyzed: string;
    pattern_strength: number;
  }> => {
    const response = await api.post('/intelligence/route-prediction', {
      plate_number: plateNumber,
      min_observations: 5,
      ...(daysAhead ? { days_ahead: daysAhead } : {}),
    });
    return response.data;
  },

  getDrift: async (plateNumber: string): Promise<{
    plate_number: string;
    drift_percent: number;
    threshold_percent: number;
    out_of_corridor_count: number;
    total_recent_observations: number;
    alert_type: string;
    pattern_analyzed_at: string;
  }> => {
    const response = await api.post('/intelligence/route-prediction/pattern-drift', null, {
      params: { plate_number: plateNumber },
    });
    return response.data;
  },

  getRecurring: async (): Promise<Array<{
    plate_number: string;
    recurrence_score: number;
    pattern_strength: number;
    primary_corridor: Array<[number, number]>;
    predominant_direction: string;
    observation_count: number;
    analyzed_at: string;
    alert_type: string;
  }>> => {
    const response = await api.get('/intelligence/route-prediction/recurring-alerts');
    return response.data;
  },

  // Convoys & Roaming
  getConvoys: async (plateNumber?: string): Promise<Array<{
    id: string;
    algorithm_type: string;
    observation_id: string;
    decision: string;
    confidence: number;
    severity: string;
    explanation: string;
    false_positive_risk: number;
    metrics: {
      related_plate: string;
      cooccurrence_count: number;
    };
    created_at: string;
  }>> => {
    const response = await api.get('/intelligence/convoys', {
      params: plateNumber ? { plate_number: plateNumber } : undefined,
    });
    // Converter false_positive_risk de string para number
    return response.data.map((item: any) => ({
      ...item,
      false_positive_risk: parseFloat(item.false_positive_risk),
    }));
  },

  getRoaming: async (plateNumber?: string): Promise<Array<{
    id: string;
    algorithm_type: string;
    observation_id: string;
    decision: string;
    confidence: number;
    severity: string;
    explanation: string;
    false_positive_risk: number;
    metrics: {
      area_label: string;
      recurrence_count: number;
    };
    created_at: string;
  }>> => {
    const response = await api.get('/intelligence/roaming', {
      params: plateNumber ? { plate_number: plateNumber } : undefined,
    });
    // Converter false_positive_risk de string para number
    return response.data.map((item: any) => ({
      ...item,
      false_positive_risk: parseFloat(item.false_positive_risk),
    }));
  },
};

// Dashboard/Analytics API
export const dashboardApi = {
  getStats: async (agencyId?: string): Promise<DashboardStats> => {
    const params = agencyId ? { agency_id: agencyId } : {};
    const response = await api.get('/intelligence/analytics/overview', { params });
    return response.data;
  },

  getAgencies: async (agencyType?: string): Promise<{ agencies: Agency[]; total: number }> => {
    const params = agencyType ? { agency_type: agencyType } : {};
    const response = await api.get('/intelligence/agencies', { params });
    return response.data;
  },

  getObservationsByDay: async (days: number = 7): Promise<Array<{
    date: string;
    count: number;
  }>> => {
    const response = await api.get('/intelligence/analytics/observations-by-day', {
      params: { days },
    });
    return response.data;
  },

  getTopPlates: async (limit: number = 10): Promise<Array<{
    plate_number: string;
    observation_count: number;
    suspicion_count: number;
  }>> => {
    const response = await api.get('/intelligence/analytics/top-plates', {
      params: { limit },
    });
    return response.data;
  },

  getUnitPerformance: async (): Promise<Array<{
    unit_name: string;
    observation_count: number;
    suspicion_rate: number;
  }>> => {
    const response = await api.get('/intelligence/analytics/unit-performance');
    return response.data;
  },
};


// Suspicion Reports API
export const suspicionApi = {
  listReports: async (filters?: {
    status?: string;
    agent_id?: string;
    plate_number?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    reports: Array<{
      id: string;
      observation_id: string;
      agent_id: string;
      agent_name: string;
      plate_number: string;
      suspicion_reason: string;
      suspicion_level: string;
      status: string;
      created_at: string;
      updated_at: string;
      feedback_count: number;
      has_second_approach: boolean;
    }>;
    total: number;
    page: number;
    page_size: number;
  }> => {
    const response = await api.get('/suspicion/reports', { params: filters });
    return response.data;
  },

  createReport: async (data: {
    observation_id: string;
    suspicion_reason: string;
    suspicion_level: string;
    notes?: string;
    evidence?: {
      image_url?: string;
      audio_url?: string;
    };
  }): Promise<any> => {
    const response = await api.post('/suspicion/reports', data);
    return response.data;
  },

  getReport: async (id: string): Promise<any> => {
    const response = await api.get(`/suspicion/reports/${id}`);
    return response.data;
  },

  updateReport: async (id: string, data: {
    suspicion_reason?: string;
    suspicion_level?: string;
    notes?: string;
  }): Promise<any> => {
    const response = await api.patch(`/suspicion/reports/${id}`, data);
    return response.data;
  },

  addFeedback: async (id: string, data: {
    feedback_type: string;
    message: string;
    rating?: number;
  }): Promise<any> => {
    const response = await api.post(`/suspicion/reports/${id}/feedback`, data);
    return response.data;
  },

  createSecondApproach: async (id: string, data: {
    approach_notes: string;
    outcome: string;
    evidence?: {
      image_url?: string;
      audio_url?: string;
    };
  }): Promise<any> => {
    const response = await api.post(`/suspicion/reports/${id}/second-approach`, data);
    return response.data;
  },

  closeReport: async (id: string, data: {
    closing_reason: string;
    final_outcome: string;
  }): Promise<any> => {
    const response = await api.post(`/suspicion/reports/${id}/close`, data);
    return response.data;
  },

  reopenReport: async (id: string, data: {
    reopening_reason: string;
  }): Promise<any> => {
    const response = await api.post(`/suspicion/reports/${id}/reopen`, data);
    return response.data;
  },

  batchCreateReports: async (reports: Array<any>): Promise<{
    created: number;
    failed: number;
    errors: Array<{ index: number; error: string }>;
  }> => {
    const response = await api.post('/suspicion/reports/batch', { reports });
    return response.data;
  },

  searchReports: async (query: {
    q: string;
    filters?: Record<string, any>;
  }): Promise<any> => {
    const response = await api.get('/suspicion/reports/search', { params: query });
    return response.data;
  },

  getStatistics: async (filters?: {
    date_from?: string;
    date_to?: string;
    agent_id?: string;
  }): Promise<{
    total_reports: number;
    by_status: Record<string, number>;
    by_level: Record<string, number>;
    by_reason: Record<string, number>;
    confirmation_rate: number;
    avg_resolution_time_hours: number;
  }> => {
    const response = await api.get('/suspicion/reports/statistics', { params: filters });
    return response.data;
  },

  exportReports: async (format: 'pdf' | 'xlsx' | 'csv', filters?: any): Promise<Blob> => {
    const response = await api.get(`/suspicion/reports/export`, {
      params: { format, ...filters },
      responseType: 'blob'
    });
    return response.data;
  },
};

// Agents Management API
export const agentsApi = {
  listAgents: async (filters?: {
    agency_id?: string;
    unit_id?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    agents: Array<{
      id: string;
      name: string;
      email: string;
      phone: string;
      badge_number: string;
      role: string;
      status: string;
      agency_id: string;
      agency_name: string;
      unit_id?: string;
      unit_name?: string;
      last_login?: string;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }> => {
    const response = await api.get('/agents', { params: filters });
    return response.data;
  },

  getAgent: async (id: string): Promise<any> => {
    const response = await api.get(`/agents/${id}`);
    return response.data;
  },

  updateAgentStatus: async (id: string, data: {
    status: string;
    reason?: string;
  }): Promise<any> => {
    const response = await api.patch(`/agents/${id}/status`, data);
    return response.data;
  },

  updateAgentLocation: async (id: string, data: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    heading?: number;
    speed?: number;
  }): Promise<any> => {
    const response = await api.post(`/agents/${id}/location`, data);
    return response.data;
  },
};

// Devices API
export const devicesApi = {
  listDevices: async (filters?: {
    agent_id?: string;
    status?: string;
    device_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    devices: Array<{
      id: string;
      device_id: string;
      device_type: string;
      model: string;
      os_version: string;
      app_version: string;
      agent_id?: string;
      agent_name?: string;
      status: string;
      last_heartbeat?: string;
      battery_level?: number;
      location?: {
        latitude: number;
        longitude: number;
        accuracy: number;
      };
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }> => {
    const response = await api.get('/devices', { params: filters });
    return response.data;
  },

  sendHeartbeat: async (deviceId: string, data: {
    battery_level?: number;
    location?: {
      latitude: number;
      longitude: number;
      accuracy: number;
    };
    network_status?: string;
  }): Promise<any> => {
    const response = await api.post(`/devices/${deviceId}/heartbeat`, data);
    return response.data;
  },
};

// Monitoring API
export const monitoringApi = {
  getHealth: async (): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp: string;
    services: Array<{
      name: string;
      status: string;
      response_time_ms: number;
      last_check: string;
    }>;
    database: {
      status: string;
      connections: number;
      response_time_ms: number;
    };
    redis: {
      status: string;
      connections: number;
      memory_usage_mb: number;
    };
  }> => {
    const response = await api.get('/monitoring/health');
    return response.data;
  },

  getMetrics: async (): Promise<{
    system: {
      cpu_usage_percent: number;
      memory_usage_percent: number;
      disk_usage_percent: number;
      uptime_seconds: number;
    };
    api: {
      requests_per_minute: number;
      avg_response_time_ms: number;
      error_rate_percent: number;
      active_connections: number;
    };
    database: {
      queries_per_second: number;
      avg_query_time_ms: number;
      active_connections: number;
      slow_queries_count: number;
    };
    cache: {
      hit_rate_percent: number;
      memory_usage_mb: number;
      keys_count: number;
      evictions_per_minute: number;
    };
  }> => {
    const response = await api.get('/monitoring/metrics');
    return response.data;
  },

  getPerformance: async (timeRange?: '1h' | '6h' | '24h' | '7d'): Promise<{
    time_range: string;
    metrics: Array<{
      timestamp: string;
      cpu_usage: number;
      memory_usage: number;
      api_response_time: number;
      database_response_time: number;
      error_rate: number;
      requests_per_minute: number;
    }>;
    summary: {
      avg_cpu_usage: number;
      avg_memory_usage: number;
      avg_response_time: number;
      total_requests: number;
      error_rate: number;
    };
  }> => {
    const response = await api.get('/monitoring/performance', { 
      params: timeRange ? { time_range: timeRange } : undefined 
    });
    return response.data;
  },
};

// WebSocket API
export const websocketApi = {
  connect: (onMessage: (data: any) => void, onError?: (error: Event) => void) => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Auto-reconnect after 5 seconds
      setTimeout(() => {
        websocketApi.connect(onMessage, onError);
      }, 5000);
    };
    
    return ws;
  },
  
  subscribe: (ws: WebSocket, channels: string[]) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels
      }));
    }
  },
  
  unsubscribe: (ws: WebSocket, channels: string[]) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'unsubscribe',
        channels
      }));
    }
  },
};

// INTERCEPT Algorithm API
export const interceptApi = {
  getInterceptEvents: async (params?: {
    recommendation?: string;
    priority_level?: string;
    limit?: number;
  }) => {
    const response = await api.get('/intelligence/intercept/events', { params });
    return response.data;
  },
};

export default api;
