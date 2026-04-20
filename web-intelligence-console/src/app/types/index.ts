// F.A.R.O. Web Intelligence Console - TypeScript Types

export type UserRole = 'field_agent' | 'intelligence' | 'supervisor' | 'admin';

export type SuspicionLevel = 'low' | 'medium' | 'high';
export type UrgencyLevel = 'monitor' | 'intelligence' | 'approach';
export type SuspicionReason = 
  | 'stolen_vehicle' 
  | 'suspicious_behavior' 
  | 'wanted_plate' 
  | 'unusual_hours'
  | 'known_associate'
  | 'drug_trafficking'
  | 'weapons'
  | 'gang_activity'
  | 'other';

export type ReviewStatus = 'pending' | 'confirmed' | 'discarded' | 'monitoring';
export type AlertType = 'instant' | 'pattern' | 'recurrence' | 'correlation';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type SyncStatus = 'pending' | 'syncing' | 'completed' | 'failed';
export type WatchlistStatus = 'active' | 'inactive' | 'archived';
export type WatchlistCategory = 'stolen' | 'suspicious' | 'wanted' | 'monitoring';
export type CaseStatus = 'open' | 'monitoring' | 'escalated' | 'closed';
export type CaseLinkType = 'observation' | 'watchlist' | 'score' | 'occurrence' | 'vehicle';
export type AnalystReviewStatus = 'draft' | 'final' | 'rectified' | 'supervisor_review';
export type AnalystConclusion = 'improcedente' | 'fraca' | 'moderada' | 'relevante' | 'critica';
export type AnalystDecision =
  | 'discarded'
  | 'in_analysis'
  | 'confirmed_monitoring'
  | 'confirmed_approach'
  | 'linked_to_case'
  | 'escalated';
export type AlgorithmDecision =
  | 'no_match'
  | 'weak_match'
  | 'relevant_match'
  | 'critical_match'
  | 'impossible'
  | 'highly_improbable'
  | 'anomalous'
  | 'discarded'
  | 'normal'
  | 'slight_deviation'
  | 'relevant_anomaly'
  | 'strong_anomaly'
  | 'low_recurrence'
  | 'medium_recurrence'
  | 'relevant_recurrence'
  | 'monitoring_recommended'
  | 'casual'
  | 'repeated'
  | 'probable_convoy'
  | 'strong_convoy'
  | 'normal_circulation'
  | 'light_roaming'
  | 'relevant_roaming'
  | 'likely_loitering'
  | 'informative'
  | 'monitor'
  | 'relevant'
  | 'high_risk'
  | 'critical';

export interface GeolocationPoint {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  cpf?: string;
  badge_number?: string;
  role: UserRole;
  agency_id?: string;
  agency_name?: string;
  unit_id?: string;
  unit_name?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface VehicleObservation {
  id: string;
  client_id?: string;
  plate_number: string;
  plate_state?: string;
  plate_country: string;
  observed_at_local: string;
  observed_at_server?: string;
  location: GeolocationPoint;
  heading?: number;
  speed?: number;
  vehicle_color?: string;
  vehicle_type?: string;
  vehicle_model?: string;
  vehicle_year?: number;
  sync_status: SyncStatus;
  agent_id: string;
  agent_name: string;
  device_id: string;
  created_at: string;
  updated_at: string;
  plate_reads: PlateRead[];
  instant_feedback?: InstantFeedback;
  metadata_snapshot?: Record<string, unknown>;
}

export interface PlateRead {
  id: string;
  observation_id: string;
  ocr_raw_text: string;
  ocr_confidence: number;
  ocr_engine: string;
  image_url?: string;
  processed_at: string;
  processing_time_ms?: number;
}

export interface InstantFeedback {
  has_alert: boolean;
  alert_level?: string;
  alert_title?: string;
  alert_message?: string;
  previous_observations_count: number;
  is_monitored: boolean;
  intelligence_interest: boolean;
  guidance?: string;
}

export interface SuspicionReport {
  id: string;
  observation_id: string;
  reason: SuspicionReason;
  level: SuspicionLevel;
  urgency: UrgencyLevel;
  notes?: string;
  abordado?: boolean;
  nivel_abordagem?: number;
  ocorrencia_registrada?: boolean;
  texto_ocorrencia?: string;
  image_url?: string;
  audio_url?: string;
  audio_duration_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceReview {
  id: string;
  observation_id: string;
  reviewer_id: string;
  reviewer_name: string;
  status: ReviewStatus;
  justification: string;
  reviewed_at: string;
  reclassified_reason?: SuspicionReason;
  reclassified_level?: SuspicionLevel;
  reclassified_urgency?: UrgencyLevel;
  occurrence_number?: string;
  occurrence_url?: string;
}

export interface FeedbackForAgent {
  feedback_id: string;
  observation_id: string;
  plate_number: string;
  feedback_type: string;
  title: string;
  message: string;
  recommended_action?: string;
  sent_at: string;
  is_read: boolean;
  read_at?: string;
  reviewer_name: string;
}

export interface Alert {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  observation_id?: string;
  suspicion_report_id?: string;
  plate_number?: string;
  is_acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  created_at: string;
  context_data?: Record<string, unknown>;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  conditions: Record<string, unknown>;
  alert_type: AlertType;
  severity: AlertSeverity;
  priority: number;
  is_active: boolean;
  created_by: string;
  created_by_name: string;
  trigger_count: number;
  last_triggered_at?: string;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceQueueItem {
  observation_id: string;
  plate_number: string;
  observed_at: string;
  location: GeolocationPoint;
  agent_name: string;
  unit_name?: string;
  suspicion_reason: SuspicionReason;
  suspicion_level: SuspicionLevel;
  urgency: UrgencyLevel;
  suspicion_notes?: string;
  previous_observations_count: number;
  is_monitored: boolean;
  has_image: boolean;
  score_value?: number;
  score_label?: string;
  priority_source?: string;
  added_to_queue_at: string;
}

export interface RoutePattern {
  id: string;
  plate_number: string;
  observation_count: number;
  first_observed_at: string;
  last_observed_at: string;
  centroid: GeolocationPoint;
  bounding_box: GeolocationPoint[];
  corridor_points?: GeolocationPoint[];
  primary_corridor_name?: string;
  predominant_direction?: number;
  recurrence_score: number;
  pattern_strength?: 'weak' | 'moderate' | 'strong';
  common_hours?: number[];
  common_days?: number[];
  analyzed_at?: string;
}

export interface WatchlistEntry {
  id: string;
  created_by: string;
  created_by_name?: string;
  status: WatchlistStatus;
  category: WatchlistCategory;
  plate_number?: string;
  plate_partial?: string;
  vehicle_make?: string;
  vehicle_model?: string;
  vehicle_color?: string;
  visual_traits?: string;
  interest_reason: string;
  information_source?: string;
  sensitivity_level: string;
  confidence_level?: string;
  geographic_scope?: string;
  active_time_window?: string;
  priority: number;
  recommended_action?: string;
  silent_mode: boolean;
  notes?: string;
  valid_from?: string;
  valid_until?: string;
  review_due_at?: string;
  metadata_json?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceCase {
  id: string;
  title: string;
  hypothesis?: string;
  summary?: string;
  status: CaseStatus;
  sensitivity_level: string;
  priority: number;
  review_due_at?: string;
  created_by: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface CaseLink {
  id: string;
  case_id: string;
  link_type: CaseLinkType;
  linked_entity_id: string;
  linked_label?: string;
  created_by: string;
  created_by_name?: string;
  created_at: string;
}

export interface DashboardStats {
  total_observations: number;
  today_observations: number;
  pending_reviews: number;
  active_alerts: number;
  confirmed_suspicions: number;
  discarded_suspicions: number;
  avg_response_time_hours: number;
  ocr_correction_rate: number;
  critical_scores?: number;
  watchlist_hits?: number;
}

export type AgencyType = 'local' | 'regional' | 'central';

export interface Agency {
  id: string;
  name: string;
  code: string;
  type: AgencyType;
  parent_agency_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardPriorityBucket {
  label: string;
  description: string;
  count: number;
  tone: 'critical' | 'high' | 'moderate' | 'info';
}

export interface WatchlistEntry {
  id: string;
  created_by: string;
  created_by_name?: string;
  status: WatchlistStatus;
  category: WatchlistCategory;
  plate_number?: string;
  plate_partial?: string;
  vehicle_make?: string;
  vehicle_model?: string;
  vehicle_color?: string;
  visual_traits?: string;
  interest_reason: string;
  information_source?: string;
  sensitivity_level: string;
  confidence_level?: string;
  geographic_scope?: string;
  active_time_window?: string;
  priority: number;
  recommended_action?: string;
  silent_mode: boolean;
  notes?: string;
  valid_from?: string;
  valid_until?: string;
  review_due_at?: string;
  metadata_json?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AlgorithmResult {
  id: string;
  algorithm_type: string;
  observation_id?: string;
  plate_number?: string;
  decision: AlgorithmDecision;
  confidence: number;
  severity: string;
  explanation: string;
  false_positive_risk: string;
  metrics: Record<string, unknown>;
  created_at: string;
}

export interface SuspicionScoreFactor {
  factor_name: string;
  factor_source: string;
  weight: number;
  contribution: number;
  explanation: string;
  direction: string;
}

export interface SuspicionScore {
  id: string;
  observation_id: string;
  plate_number: string;
  final_score: number;
  final_label: AlgorithmDecision;
  confidence: number;
  severity: string;
  explanation: string;
  false_positive_risk: string;
  factors: SuspicionScoreFactor[];
  created_at: string;
}

export interface AnalystReview {
  id: string;
  observation_id: string;
  analyst_id: string;
  analyst_name?: string;
  status: AnalystReviewStatus;
  conclusion?: AnalystConclusion;
  decision?: AnalystDecision;
  source_quality?: string;
  data_reliability?: string;
  reinforcing_factors?: Record<string, unknown>;
  weakening_factors?: Record<string, unknown>;
  recommendation?: string;
  justification: string;
  sensitivity_level: string;
  review_due_at?: string;
  linked_case_id?: string;
  linked_occurrence_ref?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalystFeedbackEvent {
  id: string;
  observation_id?: string;
  analyst_id: string;
  analyst_name?: string;
  target_user_id?: string;
  target_team_label?: string;
  feedback_type: string;
  sensitivity_level: string;
  title: string;
  message: string;
  delivered_at?: string;
  read_at?: string;
  created_at: string;
}

export interface AnalystFeedbackTemplate {
  id: string;
  created_by: string;
  created_by_name?: string;
  name: string;
  feedback_type: string;
  sensitivity_level: string;
  body_template: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FeedbackRecipient {
  recipient_type: 'user' | 'unit';
  user_id?: string;
  user_name?: string;
  user_role?: string;
  unit_id?: string;
  unit_code?: string;
  unit_name?: string;
  target_team_label?: string;
  label: string;
}

export interface ObservationDetail extends VehicleObservation {
  algorithm_results: AlgorithmResult[];
  suspicion_score?: SuspicionScore;
  analyst_reviews: AnalystReview[];
  feedback_events: AnalystFeedbackEvent[];
  suspicion_report?: SuspicionReport;
}

export interface IntelligenceCase {
  id: string;
  title: string;
  hypothesis?: string;
  summary?: string;
  status: 'open' | 'monitoring' | 'escalated' | 'closed';
  sensitivity_level: string;
  priority: number;
  review_due_at?: string;
  created_by: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_user_id?: string;
  actor_name?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details?: Record<string, unknown>;
  justification?: string;
  created_at: string;
}

export interface AgentLocationEntry {
  id: string;
  agent_id: string;
  agent_name: string;
  location: GeolocationPoint;
  recorded_at: string;
  connectivity_status: string;
  battery_level?: number;
  accuracy_meters?: number;
  agency_id?: string;
}

export interface GeolocationAuditFilter {
  agent_id?: string;
  start_date?: string;
  end_date?: string;
  agency_id?: string;
  min_accuracy?: number;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  code?: string;
  timestamp: string;
  connection_error?: string;
  retry_after?: number;
}

export interface Device {
  id: string;
  device_id: string;
  user_id: string;
  agency_id?: string;
  device_model?: string;
  os_version?: string;
  app_version?: string;
  is_active: boolean;
  last_seen: string;
  created_at: string;
  updated_at: string;
}
