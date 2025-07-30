import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PortfolioPage from "./page";

// Mock the API module
jest.mock("@/lib/api/sites");

const mockGetSites = jest.fn();

// Mock Next.js Link component
jest.mock("next/link", () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = 'MockLink';
  return MockLink;
});

// Remove this line since we're using mockGetSites directly

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithQueryClient(component: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
}

describe("PortfolioPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set up the mock to return getSites function
    const { sitesApi } = jest.requireMock("@/lib/api/sites") as { sitesApi: { getSites: jest.Mock } };
    sitesApi.getSites = mockGetSites;
  });

  it("renders loading state initially", () => {
    mockGetSites.mockImplementation(() => new Promise(() => {}));
    
    renderWithQueryClient(<PortfolioPage />);
    
    expect(screen.getByText("Loading sites...")).toBeInTheDocument();
    expect(screen.getByRole("generic", { name: "" })).toHaveClass("animate-spin");
  });

  it("renders sites when data is loaded successfully", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE001",
          site_name: "Solar Farm Alpha",
          location: "Arizona, USA",
          capacity_kw: 5000,
          installation_date: "2023-01-15",
          status: "active",
        },
        {
          site_id: "SITE002",
          site_name: "Solar Farm Beta",
          location: "California, USA",
          capacity_kw: 3000,
          installation_date: "2023-03-20",
          status: "active",
        },
      ],
      total_count: 2,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Site Portfolio")).toBeInTheDocument();
    });

    // Check if sites are rendered
    expect(screen.getByText("Solar Farm Alpha")).toBeInTheDocument();
    expect(screen.getByText("Solar Farm Beta")).toBeInTheDocument();
    expect(screen.getByText("SITE001")).toBeInTheDocument();
    expect(screen.getByText("SITE002")).toBeInTheDocument();

    // Check site details
    expect(screen.getByText("Arizona, USA")).toBeInTheDocument();
    expect(screen.getByText("California, USA")).toBeInTheDocument();
    expect(screen.getByText("5,000 kW")).toBeInTheDocument();
    expect(screen.getByText("3,000 kW")).toBeInTheDocument();

    // Check total capacity calculation
    expect(screen.getByText("8,000 kW Total Capacity")).toBeInTheDocument();
    expect(screen.getByText("2 Active Sites")).toBeInTheDocument();

    // Check navigation links
    const viewButtons = screen.getAllByText("View Performance");
    expect(viewButtons).toHaveLength(2);
  });

  it("renders empty state when no sites are available", async () => {
    const mockEmptyData = {
      sites: [],
      total_count: 0,
    };

    mockGetSites.mockResolvedValue(mockEmptyData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("No Sites Found")).toBeInTheDocument();
    });

    expect(screen.getByText("There are no active solar sites to display.")).toBeInTheDocument();
    expect(screen.getByText("0 Active Sites")).toBeInTheDocument();
    expect(screen.getByText("0 kW Total Capacity")).toBeInTheDocument();
  });

  it("renders error state when API call fails", async () => {
    const errorMessage = "Failed to fetch sites";
    mockGetSites.mockRejectedValue(new Error(errorMessage));

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Error Loading Sites")).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.getByText("Try Again")).toBeInTheDocument();
  });

  it("handles sites with missing optional fields", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE003",
          // Missing optional fields
        },
      ],
      total_count: 1,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("SITE003")).toBeInTheDocument();
    });

    // Should display site_id as name when site_name is missing
    expect(screen.getByText("SITE003")).toBeInTheDocument();
    
    // Should handle missing capacity in total calculation
    expect(screen.getByText("0 kW Total Capacity")).toBeInTheDocument();
  });

  it("formats dates correctly", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE001",
          site_name: "Solar Farm Alpha",
          installation_date: "2023-01-15",
        },
      ],
      total_count: 1,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Solar Farm Alpha")).toBeInTheDocument();
    });

    // Check if date is formatted correctly
    const formattedDate = new Date("2023-01-15").toLocaleDateString();
    expect(screen.getByText(formattedDate)).toBeInTheDocument();
  });

  it("formats capacity numbers correctly", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE001",
          capacity_kw: 12500.5,
        },
      ],
      total_count: 1,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("SITE001")).toBeInTheDocument();
    });

    // Check if capacity is formatted with commas
    expect(screen.getByText("12,500.5 kW")).toBeInTheDocument();
    expect(screen.getByText("12,500.5 kW Total Capacity")).toBeInTheDocument();
  });

  it("generates correct navigation links", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE001",
          site_name: "Solar Farm Alpha",
        },
      ],
      total_count: 1,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Solar Farm Alpha")).toBeInTheDocument();
    });

    // Check if navigation link is correct
    const link = screen.getByRole("link", { name: /View Performance/ });
    expect(link).toHaveAttribute("href", "/portfolio/SITE001");
  });

  it("has accessible navigation elements", async () => {
    const mockSitesData = {
      sites: [
        {
          site_id: "SITE001",
          site_name: "Solar Farm Alpha",
        },
      ],
      total_count: 1,
    };

    mockGetSites.mockResolvedValue(mockSitesData);

    renderWithQueryClient(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Solar Farm Alpha")).toBeInTheDocument();
    });

    // Check for accessible elements
    expect(screen.getByRole("button", { name: /View Performance/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to Home/ })).toBeInTheDocument();
  });
});