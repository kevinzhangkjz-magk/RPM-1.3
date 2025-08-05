export const mockGetSites = jest.fn();
export const mockGetSitePerformance = jest.fn();

export const sitesApi = {
  getSites: mockGetSites,
  getSitePerformance: mockGetSitePerformance,
};

export const sitesQueryKeys = {
  all: ["sites"] as const,
  lists: () => ["sites", "list"] as const,
  performance: () => ["sites", "performance"] as const,
  sitePerformance: (siteId: string) => ["sites", "performance", siteId] as const,
};