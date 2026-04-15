// F.A.R.O. Web Intelligence Console - API Service
import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import {
  AnalystConclusion,
  AnalystDecision,
  AnalystFeedbackEvent,
  AnalystFeedbackTemplate,
  FeedbackRecipient,
  AnalystReview,
  AnalystReviewStatus,
  AlgorithmResult,
  User,
  VehicleObservation,
  ObservationDetail,
  IntelligenceQueueItem,
  FeedbackForAgent,
  Alert,
  AlertRule,
  RoutePattern,
  DashboardStats,
  WatchlistEntry,
  WatchlistCategory,
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
} from '@/app/types';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

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
    const response = await api.get('/alerts', { params: { ...filters, ...pagination } });
    return response.data;
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
};

// Dashboard/Analytics API
export const dashboardApi = {
  getStats: async (agencyId?: string): Promise<DashboardStats> => {
    const params = agencyId ? { agency_id: agencyId } : {};
    const response = await api.get('/intelligence/analytics/overview', { params });
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
    unit_id: string;
    unit_name: string;
    observation_count: number;
    confirmation_rate: number;
  }>> => {
    const response = await api.get('/intelligence/analytics/unit-performance');
    return response.data;
  },
};

export default api;
