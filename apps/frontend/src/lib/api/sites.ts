import { SitesResponse, SitePerformanceResponse, SkidsResponse, ApiError } from "@/types/site";
import { AIQueryRequest, AIQueryResponse } from "@/types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";


class ApiClient {
  private baseUrl: string;
  private credentials: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    // For demo purposes, using hardcoded credentials
    // In production, this should come from secure authentication
    this.credentials = btoa("testuser:testpass");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Basic ${this.credentials}`,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData: ApiError = await response.json();
          if (errorData.message) {
            errorMessage = errorData.message;
          } else if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (errorData.detail.message) {
              errorMessage = errorData.detail.message;
            }
          }
        } catch {
          // If response is not JSON, use default error message
        }
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("An unexpected error occurred");
    }
  }

  async getSites(): Promise<SitesResponse> {
    return await this.request<SitesResponse>("/api/sites/");
  }

  async getSitePerformance(siteId: string, startDate?: string, endDate?: string): Promise<SitePerformanceResponse> {
    try {
      // If dates are provided, use them directly
      if (startDate && endDate) {
        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate
        });
        
        console.log(`Fetching performance data for site: ${siteId}`, {
          start_date: startDate,
          end_date: endDate,
          url: `/api/sites/${siteId}/performance?${params}`
        });
        
        return await this.request<SitePerformanceResponse>(`/api/sites/${siteId}/performance?${params}`);
      }

      // Smart defaulting: try current month first, then fall back to previous month
      const now = new Date();
      const currentMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      const currentMonthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
      
      // If current month end is in the future, use current time instead
      const safeCurrentEnd = currentMonthEnd > now ? new Date(now.getTime() - 60000) : currentMonthEnd;
      
      try {
        // Try current month first
        const currentParams = new URLSearchParams({
          start_date: currentMonth.toISOString(),
          end_date: safeCurrentEnd.toISOString()
        });
        
        console.log(`Trying current month data for site: ${siteId}`, {
          start_date: currentMonth.toISOString(),
          end_date: safeCurrentEnd.toISOString()
        });
        
        const currentMonthResponse = await this.request<SitePerformanceResponse>(`/api/sites/${siteId}/performance?${currentParams}`);
        
        // If we have data points, return current month data
        if (currentMonthResponse.data_points && currentMonthResponse.data_points.length > 0) {
          return currentMonthResponse;
        }
        
        // No data in current month, fall back to previous month
        throw new Error('No data in current month');
        
      } catch {
        // Fall back to previous month
        const previousMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const previousMonthEnd = new Date(previousMonth.getFullYear(), previousMonth.getMonth() + 1, 0, 23, 59, 59);
        
        const fallbackParams = new URLSearchParams({
          start_date: previousMonth.toISOString(),
          end_date: previousMonthEnd.toISOString()
        });
        
        console.log(`Falling back to previous month data for site: ${siteId}`, {
          start_date: previousMonth.toISOString(),
          end_date: previousMonthEnd.toISOString()
        });
        
        const fallbackResponse = await this.request<SitePerformanceResponse>(`/api/sites/${siteId}/performance?${fallbackParams}`);
        
        // Add metadata to indicate this is fallback data
        return {
          ...fallbackResponse,
          isFallbackData: true,
          fallbackReason: 'No data available for current month'
        } as SitePerformanceResponse & { isFallbackData: boolean; fallbackReason: string };
      }
    } catch (error) {
      throw error;
    }
  }

  async getSiteSkids(siteId: string, startDate?: string, endDate?: string): Promise<SkidsResponse> {
    // Default to previous month to ensure we have data
    const now = new Date();
    // Go back to previous month
    const previousMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const firstOfMonth = previousMonth;
    const lastOfMonth = new Date(previousMonth.getFullYear(), previousMonth.getMonth() + 1, 0, 23, 59, 59);
    
    const defaultStartDate = startDate || firstOfMonth.toISOString();
    const defaultEndDate = endDate || lastOfMonth.toISOString();
    
    const params = new URLSearchParams({
      start_date: defaultStartDate,
      end_date: defaultEndDate
    });
    
    return this.request<SkidsResponse>(`/api/sites/${siteId}/skids?${params}`);
  }

  async queryAI(request: AIQueryRequest): Promise<AIQueryResponse> {
    return this.request<AIQueryResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// React Query hooks
export const sitesQueryKeys = {
  all: ["sites"] as const,
  lists: () => [...sitesQueryKeys.all, "list"] as const,
  list: (filters: string) => [...sitesQueryKeys.lists(), { filters }] as const,
  details: () => [...sitesQueryKeys.all, "detail"] as const,
  detail: (id: string) => [...sitesQueryKeys.details(), id] as const,
  performance: () => [...sitesQueryKeys.all, "performance"] as const,
  sitePerformance: (siteId: string) => [...sitesQueryKeys.performance(), siteId] as const,
  skids: () => [...sitesQueryKeys.all, "skids"] as const,
  siteSkids: (siteId: string) => [...sitesQueryKeys.skids(), siteId] as const,
  aiQuery: () => ["aiQuery"] as const,
};

export const sitesApi = {
  getSites: () => apiClient.getSites(),
  getSitePerformance: (siteId: string, startDate?: string, endDate?: string) => 
    apiClient.getSitePerformance(siteId, startDate, endDate),
  getSiteSkids: (siteId: string, startDate?: string, endDate?: string) => 
    apiClient.getSiteSkids(siteId, startDate, endDate),
  queryAI: (request: AIQueryRequest) => apiClient.queryAI(request),
};