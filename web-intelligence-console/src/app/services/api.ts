// F.A.R.O. Web Intelligence Console - API Service
import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  AnalystConclusion,
  AnalystDecision,
  AnalystFeedbackEvent,
  AnalystFeedbackTemplate,
  DashboardPriorityBucket,
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
  RouteTimeline,
  RouteComparison,
  RoutePrediction,
  RoutePredictionForPlate,
  PatternDriftAlert,
  RecurringRouteAlert,
  SuspiciousRoute,
  HotspotAnalysis,
  HotspotTimeline,
  HotspotPlates,
  AlertAggregated,
  Device,
  AgentLocationEntry,
  GeolocationAuditFilter,
} from '@/app/types';

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
    httpCache.delete(oldestKey);
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
const CIRCUIT_TIMEOUT_MS = 60000;

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
// Retry Interceptor (EXPERIMENTAL - Auto-retry on failure)
// ============================================================================
const RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504];
const RETRY_MAX_ATTEMPTS = 3;
const RETRY_BASE_DELAY_MS = 1000;

function shouldRetryResponse(status: number): boolean {
  return RETRY_STATUS_CODES.includes(status);
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
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Auth + Cache
api.interceptors.request.use(
  (config) => {
    // Auth token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Check for cached response (GET only)
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
    console.error('[API Error Interceptor Called]');

    // Safety check: ensure error is an object
    if (!error || typeof error !== 'object') {
      console.error('[API Error] Invalid error object');
      return Promise.reject(error);
    }

    const status = error.response?.status;
    const url = error.config?.url;
    const code = error.code;
    const message = error.message;

    console.error('[API Error] URL:', url, 'Status:', status, 'Code:', code, 'Message:', message);

    recordCircuitFailure('network');

    if (status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }

    if (error.response) {
      const apiError = error.response.data as ApiError;
      apiError.connection_error = getConnectionErrorMessage(error);
    } else {
      (error.response as unknown as ApiError) = {
        detail: getConnectionErrorMessage(error),
      } as ApiError;
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
  return axiosError.response.data?.detail || 'Erro desconhecido.';
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
      items: response.data.alerts,
      total_count: response.data.total_alerts,
      page: pagination?.page || 1,
      page_size: pagination?.limit || 100,
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

// User Management API
export const userApi = {
  listUsers: async (params?: { role?: string; agency_id?: string; page?: number; page_size?: number }) => {
    const response = await api.get('/auth/users', { params });
    return response.data;
  },

  createUser: async (userData: any) => {
    const response = await api.post('/auth/users', userData);
    return response.data;
  },

  updateUser: async (userId: string, userData: any) => {
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

// Devices API
export const devicesApi = {
  listDevices: async (): Promise<Device[]> => {
    const response = await api.get('/intelligence/devices');
    return response.data;
  },

  suspendDevice: async (deviceId: string, justification: string): Promise<Device> => {
    const response = await api.patch(`/intelligence/devices/${deviceId}/suspend`, { justification });
    return response.data;
  },
};

export default api;
