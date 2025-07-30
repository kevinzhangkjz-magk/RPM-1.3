export interface Site {
  site_id: string;
  site_name?: string;
  location?: string;
  capacity_kw?: number;
  installation_date?: string;
  status?: string;
}

export interface SitesResponse {
  sites: Site[];
  total_count: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}