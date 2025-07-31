import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SiteAnalysisPage from "./page";

// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  } as Response)
);

// Mock Next.js hooks and components
jest.mock("next/navigation", () => ({
  useParams: jest.fn(),
}));

jest.mock("next/link", () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = 'MockLink';
  return MockLink;
});

// Mock Recharts components
jest.mock("recharts", () => ({
  Scatter: ({ name }: { name: string }) => <div data-testid={`scatter-${name.toLowerCase().replace(' ', '-')}`}>{name}</div>,
  Line: ({ name }: { name?: string }) => <div data-testid="line-expected-trend">{name || 'Expected Trend'}</div>,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  ComposedChart: ({ children }: { children: React.ReactNode }) => <div data-testid="composed-chart">{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: ({ children, name }: { children?: React.ReactNode; name: string }) => <div data-testid={`bar-${name.toLowerCase().replace(' ', '-')}`}>{name}{children}</div>,
  Cell: () => <div data-testid="cell" />,
}));

// Mock API functions
const mockGetSites = jest.fn();
const mockGetSitePerformance = jest.fn();
const mockGetSiteSkids = jest.fn();

jest.mock("@/lib/api/sites", () => ({
  sitesApi: {
    getSites: () => mockGetSites(),
    getSitePerformance: () => mockGetSitePerformance(),
    getSiteSkids: () => mockGetSiteSkids(),
  },
  sitesQueryKeys: {
    lists: () => ["sites", "list"],
    sitePerformance: (siteId: string) => ["sites", "performance", siteId],
    siteSkids: (siteId: string) => ["sites", "skids", siteId],
  },
}));

import { useParams } from "next/navigation";

const mockUseParams = useParams as jest.Mock;

const mockSitesData = {
  sites: [
    {
      site_id: "SITE001",
      site_name: "Test Site",
      connectivity_status: "connected",
    },
  ],
  total_count: 1,
};

const mockPerformanceData = {
  site_id: "SITE001",
  data_points: [
    { poa_irradiance: 100, actual_power: 150, expected_power: 160 },
    { poa_irradiance: 200, actual_power: 300, expected_power: 310 },
  ],
  rmse: 1.2,
  r_squared: 0.95,
};

const mockSkidsData = {
  site_id: "SITE001",
  skids: [
    {
      skid_id: "SKID01",
      skid_name: "Skid 01",
      avg_actual_power: 1500,
      avg_expected_power: 1600,
      deviation_percentage: -6.25,
      data_point_count: 100,
    },
    {
      skid_id: "SKID02",
      skid_name: "Skid 02",
      avg_actual_power: 1550,
      avg_expected_power: 1500,
      deviation_percentage: 3.33,
      data_point_count: 105,
    },
  ],
  total_count: 2,
};

const renderWithQuery = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe("SiteAnalysisPage - Skids View", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSites.mockResolvedValue(mockSitesData);
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);
    mockGetSiteSkids.mockResolvedValue(mockSkidsData);
  });

  it("renders site view by default", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByText("Power Curve - Site: SITE001")).toBeInTheDocument();
    expect(screen.getByText("Actual vs. Expected Performance Analysis")).toBeInTheDocument();
  });

  it("shows interactive skid performance section", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      expect(screen.getByText("Skid Performance")).toBeInTheDocument();
      expect(screen.getByText("View All Skids")).toBeInTheDocument();
    });
  });

  it("switches to skids view when clicking View All Skids button", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Skid Performance - Site: SITE001")).toBeInTheDocument();
      expect(screen.getByText("Comparative Analysis of All Skids")).toBeInTheDocument();
    });
  });

  it("shows correct breadcrumbs in skids view", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Portfolio > Test Site > Skids")).toBeInTheDocument();
    });
  });

  it("displays skids comparative chart when in skids view", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Skid Comparative Analysis")).toBeInTheDocument();
      expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
    });
  });

  it("shows site summary in skids view sidebar", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Site Summary")).toBeInTheDocument();
      expect(screen.getByText("Total Skids:")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("highlights underperforming skids in sidebar", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Underperforming Skids")).toBeInTheDocument();
      expect(screen.getByText("Skid 01")).toBeInTheDocument(); // This should be underperforming
    });
  });

  it("shows top performers in sidebar", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Top Performers")).toBeInTheDocument();
      expect(screen.getByText("Skid 02")).toBeInTheDocument(); // This should be performing well
    });
  });

  it("allows switching back to site view", async () => {
    renderWithQuery(<SiteAnalysisPage />);

    // Switch to skids view
    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    // Switch back to site view
    await waitFor(() => {
      const backButton = screen.getByText("Back to Site Analysis");
      fireEvent.click(backButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Power Curve - Site: SITE001")).toBeInTheDocument();
      expect(screen.getByText("RMSE")).toBeInTheDocument();
      expect(screen.getByText("R-Squared")).toBeInTheDocument();
    });
  });

  it("shows loading state for skids data", async () => {
    mockGetSiteSkids.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    expect(screen.getByText("Loading skids data...")).toBeInTheDocument();
  });

  it("shows error state for skids data", async () => {
    mockGetSiteSkids.mockRejectedValue(new Error("API Error"));
    
    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      const viewSkidsButton = screen.getByText("View All Skids");
      fireEvent.click(viewSkidsButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Error loading skids data")).toBeInTheDocument();
    });
  });
});