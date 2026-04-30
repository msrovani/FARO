// F.A.R.O. Web Intelligence Console - Mobile API Service
import axios, { AxiosInstance } from 'axios';
import api from './api';
import logger from '@/app/utils/logger';
import {
  VehicleObservation,
  PaginatedResponse,
  PaginationParams,
  ObservationDetail,
  FeedbackForAgent,
} from '@/app/types';

// Mobile API for field agent operations
export const mobileApi = {
  // Get observation history for mobile agents
  getHistory: async (params?: PaginationParams): Promise<PaginatedResponse<VehicleObservation>> => {
    try {
      const response = await api.get('/mobile/history', { params });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch mobile history:', error);
      throw error;
    }
  },

  // Get specific observation details
  getObservation: async (id: string): Promise<ObservationDetail> => {
    try {
      const response = await api.get(`/mobile/observations/${id}`);
      return response.data;
    } catch (error) {
      logger.error(`Failed to fetch observation ${id}:`, error);
      throw error;
    }
  },

  // Get feedback for specific observation
  getFeedback: async (observationId: string): Promise<FeedbackForAgent[]> => {
    try {
      const response = await api.get(`/mobile/observations/${observationId}/feedback`);
      return response.data;
    } catch (error) {
      logger.error(`Failed to fetch feedback for observation ${observationId}:`, error);
      throw error;
    }
  },

  // Submit approach confirmation for observation
  submitApproachConfirmation: async (observationId: string, data: {
    confirmed_suspicion: boolean;
    approach_outcome: string;
    notes?: string;
    approached_at_local: string;
    location?: { latitude: number; longitude: number };
    suspicion_level_slider?: number;
    was_approached?: boolean;
    has_incident?: boolean;
    street_direction?: string;
  }): Promise<{ observation_id: string; plate_number: string; processed_at: string }> => {
    try {
      const response = await api.post(`/mobile/observations/${observationId}/approach-confirmation`, data);
      return response.data;
    } catch (error) {
      logger.error(`Failed to submit approach confirmation for observation ${observationId}:`, error);
      throw error;
    }
  },

  // Renew agent shift
  renewShift: async (data: {
    shift_duration_hours: number;
  }): Promise<{ message: string; renewed_until: string }> => {
    try {
      const response = await api.post('/mobile/shift-renewal', data);
      return response.data;
    } catch (error) {
      logger.error('Failed to renew shift:', error);
      throw error;
    }
  },

  // Batch upload agent locations
  uploadLocationBatch: async (data: {
    items: Array<{
      latitude: number;
      longitude: number;
      accuracy?: number;
      timestamp: string;
      battery_level?: number;
    }>;
    device_id: string;
  }): Promise<{ message: string; processed_count: number }> => {
    try {
      const response = await api.post('/mobile/agent-location/batch', data);
      return response.data;
    } catch (error) {
      logger.error('Failed to upload location batch:', error);
      throw error;
    }
  },

  // Validate plate via OCR
  validatePlate: async (data: {
    plate_number: string;
    confidence: number;
    ocr_text: string;
    image_metadata?: {
      width: number;
      height: number;
      format: string;
    };
  }): Promise<{
    is_valid: boolean;
    normalized_plate: string;
    confidence_score: number;
    suggestions?: string[];
  }> => {
    try {
      const response = await api.post('/mobile/plate-validation', data);
      return response.data;
    } catch (error) {
      logger.error('Failed to validate plate:', error);
      throw error;
    }
  },

  // Batch plate validation
  validatePlateBatch: async (data: {
    plates: Array<{
      plate_number: string;
      confidence: number;
      ocr_text: string;
      timestamp: string;
    }>;
  }): Promise<{
    results: Array<{
      plate_number: string;
      is_valid: boolean;
      normalized_plate: string;
      confidence_score: number;
    }>;
    processed_count: number;
  }> => {
    try {
      const response = await api.post('/mobile/plate-validation/batch', data);
      return response.data;
    } catch (error) {
      logger.error('Failed to validate plate batch:', error);
      throw error;
    }
  },

  // Check plate suspicion
  checkPlateSuspicion: async (plateNumber: string, data?: {
    location?: { latitude: number; longitude: number };
    context?: string;
  }): Promise<{
    plate_number: string;
    is_suspect: boolean;
    alert_level?: string;
    alert_title?: string;
    alert_message?: string;
    suspicion_reason?: string;
    suspicion_level?: string;
    previous_observations_count: number;
    is_monitored: boolean;
    intelligence_interest: boolean;
    has_active_watchlist: boolean;
    watchlist_category?: string;
    guidance?: string;
    requires_approach_confirmation: boolean;
    first_suspicion_agent_name?: string;
    first_suspicion_observation_id?: string;
    first_suspicion_at?: string;
  }> => {
    try {
      const response = await api.post(`/mobile/plate-suspicion-check`, {
        plate_number: plateNumber,
        ...data
      });
      return response.data;
    } catch (error) {
      logger.error(`Failed to check suspicion for plate ${plateNumber}:`, error);
      throw error;
    }
  },

  // Upload observation asset
  uploadAsset: async (observationId: string, file: File, assetType: string): Promise<{
    asset_id: string;
    observation_id: string;
    asset_type: string;
    storage_bucket: string;
    storage_key: string;
    content_type: string;
    size_bytes: number;
    checksum_sha256: string;
  }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', assetType);

      const response = await api.post(`/mobile/observations/${observationId}/assets`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      logger.error(`Failed to upload asset for observation ${observationId}:`, error);
      throw error;
    }
  },

  // Progressive asset upload
  uploadAssetProgressive: async (
    observationId: string,
    file: File,
    assetType: string,
    chunkIndex: number,
    uploadId?: string,
    complete: boolean = false,
    parts?: string[]
  ): Promise<{
    upload_id?: string;
    chunk_index: number;
    complete: boolean;
    parts?: string[];
  }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', assetType);
      formData.append('chunk_index', chunkIndex.toString());
      formData.append('complete', complete.toString());
      
      if (uploadId) {
        formData.append('upload_id', uploadId);
      }
      
      if (parts) {
        formData.append('parts', JSON.stringify(parts));
      }

      const response = await api.post(`/mobile/observations/${observationId}/assets/progressive`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      logger.error(`Failed to upload progressive asset for observation ${observationId}:`, error);
      throw error;
    }
  },

  // Download asset
  downloadAsset: async (bucket: string, key: string): Promise<Blob> => {
    try {
      const response = await api.get(`/mobile/assets/${bucket}/${key}`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      logger.error(`Failed to download asset ${bucket}/${key}:`, error);
      throw error;
    }
  },
};
