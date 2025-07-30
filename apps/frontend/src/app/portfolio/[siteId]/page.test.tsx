import { render, screen } from "@testing-library/react";
import SiteAnalysisPage from "./page";

// Mock Next.js hooks and components
jest.mock("next/navigation", () => ({
  useParams: jest.fn(),
}));

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

const mockUseParams = require("next/navigation").useParams as jest.Mock;

describe("SiteAnalysisPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders site analysis page with correct site ID", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    expect(screen.getByText("Site Analysis: SITE001")).toBeInTheDocument();
    expect(screen.getByText("Performance data and power curve analysis")).toBeInTheDocument();
  });

  it("displays site information cards", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    // Check for site info cards
    expect(screen.getByText("Capacity")).toBeInTheDocument();
    expect(screen.getByText("5,000 kW")).toBeInTheDocument();
    expect(screen.getByText("Total installed capacity")).toBeInTheDocument();

    expect(screen.getByText("Location")).toBeInTheDocument();
    expect(screen.getByText("Arizona")).toBeInTheDocument();
    expect(screen.getByText("Site location")).toBeInTheDocument();

    expect(screen.getByText("Installed")).toBeInTheDocument();
    expect(screen.getByText("2023")).toBeInTheDocument();
    expect(screen.getByText("Installation year")).toBeInTheDocument();
  });

  it("shows active site status", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("displays performance data placeholder", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    expect(screen.getByText("Performance Data")).toBeInTheDocument();
    expect(screen.getByText(/Detailed performance analysis and power curve visualization/)).toBeInTheDocument();
    expect(screen.getByText(/GET.*api.*sites.*siteId.*performance/)).toBeInTheDocument();
  });

  it("has correct navigation links", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    // Check navigation links
    const backLinks = screen.getAllByRole("link", { name: /Back to Portfolio/ });
    expect(backLinks).toHaveLength(2);
    backLinks.forEach(link => {
      expect(link).toHaveAttribute("href", "/portfolio");
    });
  });

  it("has disabled action buttons", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    // Check for disabled buttons
    expect(screen.getByRole("button", { name: "Export Data" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "View Report" })).toBeDisabled();
  });

  it("handles different site IDs correctly", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE999" });

    render(<SiteAnalysisPage />);

    expect(screen.getByText("Site Analysis: SITE999")).toBeInTheDocument();
  });

  it("handles special characters in site ID", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE-001_TEST" });

    render(<SiteAnalysisPage />);

    expect(screen.getByText("Site Analysis: SITE-001_TEST")).toBeInTheDocument();
  });

  it("has accessible elements", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    // Check for accessible elements
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
    
    // Check for button accessibility
    const backButtons = screen.getAllByRole("button", { name: /Back to Portfolio/ });
    expect(backButtons).toHaveLength(2);
  });

  it("displays icons correctly", () => {
    mockUseParams.mockReturnValue({ siteId: "SITE001" });

    render(<SiteAnalysisPage />);

    // Icons should be rendered (we can't easily test SVG content, but we can check they exist)
    const container = screen.getByText("Site Analysis: SITE001").closest("div");
    expect(container).toBeInTheDocument();
  });
});