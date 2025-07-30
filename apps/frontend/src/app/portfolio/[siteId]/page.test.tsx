import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SiteAnalysisPage from "./page";
import { mockGetSitePerformance } from "@/__mocks__/@/lib/api/sites";

// Mock fetch globally
global.fetch = jest.fn();

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
  ScatterChart: ({ children }: { children: React.ReactNode }) => <div data-testid="scatter-chart">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Scatter: ({ name }: { name: string }) => <div data-testid={`scatter-${name.toLowerCase().replace(' ', '-')}`}>{name}</div>,
  Line: ({ name }: { name?: string }) => <div data-testid="line-expected-trend">{name || 'Expected Trend'}</div>,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

import { useParams } from "next/navigation";

const mockUseParams = useParams as jest.Mock;

const mockPerformanceData = {
  site_id: "SITE001",
  data_points: [
    { poa_irradiance: 100, actual_power: 150, expected_power: 160 },
    { poa_irradiance: 200, actual_power: 300, expected_power: 310 },
    { poa_irradiance: 300, actual_power: 450, expected_power: 460 },
  ],
  rmse: 1.2,
  r_squared: 0.95,
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

describe("SiteAnalysisPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders power curve page with correct site ID", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByText("Power Curve - Site: SITE001")).toBeInTheDocument();
    expect(screen.getByText("Actual vs. Expected Performance Analysis")).toBeInTheDocument();
  });

  it("displays loading state while fetching data", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByText("Loading performance data...")).toBeInTheDocument();
  });

  it("displays error state when API call fails", async () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockRejectedValue(new Error("API Error"));

    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      expect(screen.getByText("Error loading data")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("displays KPI cards with calculated values", async () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      expect(screen.getByText("RMSE")).toBeInTheDocument();
      expect(screen.getByText("R-Squared")).toBeInTheDocument();
      // Check for calculated values (should be calculated client-side)
      expect(screen.getByText(/MW$/)).toBeInTheDocument();
    });
  });

  it("displays toggle controls for chart visibility", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByLabelText("Actual Data")).toBeInTheDocument();
    expect(screen.getByLabelText("Expected Data")).toBeInTheDocument();
    expect(screen.getByLabelText("Trend Line")).toBeInTheDocument();
  });

  it("displays POA/GHI button group", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByText("POA")).toBeInTheDocument();
    expect(screen.getByText("GHI")).toBeInTheDocument();
  });

  it("displays skid performance table", async () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    await waitFor(() => {
      expect(screen.getByText("Skid Performance")).toBeInTheDocument();
      expect(screen.getByText("Skid 01")).toBeInTheDocument();
      expect(screen.getByText("-5.1%")).toBeInTheDocument();
    });
  });

  it("has correct navigation links", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    const backLinks = screen.getAllByRole("link", { name: /Back to Portfolio/ });
    expect(backLinks).toHaveLength(2);
    backLinks.forEach(link => {
      expect(link).toHaveAttribute("href", "/portfolio");
    });
  });

  it("has disabled action buttons", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });
    mockGetSitePerformance.mockResolvedValue(mockPerformanceData);

    renderWithQuery(<SiteAnalysisPage />);

    expect(screen.getByRole("button", { name: "Export Data" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "View Report" })).toBeDisabled();
  });
});