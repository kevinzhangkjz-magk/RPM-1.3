export interface Site {
  site_id: string;
  site_name?: string;
  location?: string;
  capacity_kw?: number;
  installation_date?: string;
  status?: string;
  connectivity_status?: 'connected' | 'disconnected';
}

export interface SitesResponse {
  sites: Site[];
  total_count: number;
}

export interface ApiError {
  error?: string;
  message?: string;
  detail?: string | {
    error?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
  details?: Record<string, unknown>;
}

export interface PerformanceDataPoint {
  timestamp: string;
  site_id: string;
  poa_irradiance: number;
  actual_power: number;
  expected_power: number;
  inverter_availability: number;
  site_name: string | null;
  // Additional fields that might be present after transformation
  date?: string;
  predicted_power?: number;
  skid_id?: string;
}

export interface SitePerformanceSummary {
  data_point_count: number;
  start_date: string;
  end_date: string;
  avg_actual_power: number;
  avg_expected_power: number;
  total_actual_energy: number;
  total_expected_energy: number;
  performance_ratio: number;
}

export interface SitePerformanceResponse {
  site_id: string;
  site_name?: string;
  data_points: PerformanceDataPoint[];
  summary: SitePerformanceSummary;
  rmse: number;
  r_squared: number;
  // Legacy field for backward compatibility
  data?: PerformanceDataPoint[];
  // Fallback data indicators
  isFallbackData?: boolean;
  fallbackReason?: string;
}

export interface SkidPerformance {
  skid_id: string;
  skid_name: string;
  avg_actual_power: number;
  avg_expected_power: number;
  deviation_percentage: number;
  data_point_count: number;
}

export interface SkidsResponse {
  site_id: string;
  skids: SkidPerformance[];
  total_count: number;
}