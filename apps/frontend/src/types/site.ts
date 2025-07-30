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