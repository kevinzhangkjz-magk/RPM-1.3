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
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PerformanceDataPoint {
  poa_irradiance: number;
  actual_power: number;
  expected_power: number;
}

export interface SitePerformanceResponse {
  site_id: string;
  data_points: PerformanceDataPoint[];
  rmse: number;
  r_squared: number;
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