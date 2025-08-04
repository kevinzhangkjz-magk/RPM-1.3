import { render, screen } from '@testing-library/react';
import { ChatVisualization } from '../ChatVisualization';
import { ChatVisualization as ChatVisualizationType } from '@/types/chat';

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="composed-chart">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  Scatter: () => <div data-testid="scatter" />,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  Cell: () => <div data-testid="cell" />,
}));

describe('ChatVisualization', () => {
  const baseVisualization: ChatVisualizationType = {
    chart_type: 'scatter',
    data: [
      { x: 1, y: 10 },
      { x: 2, y: 20 },
      { x: 3, y: 15 },
    ],
    columns: ['x', 'y'],
  };

  it('renders scatter chart correctly', () => {
    render(<ChatVisualization visualization={baseVisualization} />);
    
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('composed-chart')).toBeInTheDocument();
    expect(screen.getByTestId('scatter')).toBeInTheDocument();
  });

  it('renders multi-scatter chart correctly', () => {
    const multiScatterVisualization: ChatVisualizationType = {
      chart_type: 'multi-scatter',
      data: [
        { x: 1, y1: 10, y2: 15 },
        { x: 2, y1: 20, y2: 25 },
      ],
      columns: ['x', 'y1', 'y2'],
    };

    render(<ChatVisualization visualization={multiScatterVisualization} />);
    
    expect(screen.getByTestId('composed-chart')).toBeInTheDocument();
    expect(screen.getAllByTestId('scatter')).toHaveLength(2);
  });

  it('renders bar chart correctly', () => {
    const barVisualization: ChatVisualizationType = {
      chart_type: 'bar',
      data: [
        { site: 'Site A', power: 100 },
        { site: 'Site B', power: 150 },
      ],
      columns: ['site', 'power'],
    };

    render(<ChatVisualization visualization={barVisualization} />);
    
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar')).toBeInTheDocument();
  });

  it('shows no data message when data is empty', () => {
    const emptyVisualization: ChatVisualizationType = {
      chart_type: 'scatter',
      data: [],
      columns: ['x', 'y'],
    };

    render(<ChatVisualization visualization={emptyVisualization} />);
    
    expect(screen.getByText('No visualization data available')).toBeInTheDocument();
    expect(screen.queryByTestId('responsive-container')).not.toBeInTheDocument();
  });

  it('shows no data message when data is null', () => {
    const nullVisualization: ChatVisualizationType = {
      chart_type: 'scatter',
      data: null,
      columns: ['x', 'y'],
    };

    render(<ChatVisualization visualization={nullVisualization} />);
    
    expect(screen.getByText('No visualization data available')).toBeInTheDocument();
  });

  it('shows no data message when data is not an array', () => {
    const invalidVisualization: ChatVisualizationType = {
      chart_type: 'scatter',
      data: { invalid: 'data' },
      columns: ['x', 'y'],
    };

    render(<ChatVisualization visualization={invalidVisualization} />);
    
    expect(screen.getByText('No visualization data available')).toBeInTheDocument();
  });

  it('shows unsupported chart type message', () => {
    const unsupportedVisualization = {
      chart_type: 'pie' as const,
      data: [{ x: 1, y: 2 }],
      columns: ['x', 'y'],
    };

    render(<ChatVisualization visualization={unsupportedVisualization as unknown as ChatVisualizationType} />);
    
    expect(screen.getByText('Unsupported chart type: pie')).toBeInTheDocument();
    // The ResponsiveContainer will still exist but contain the error message
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders chart with proper container structure', () => {
    render(<ChatVisualization visualization={baseVisualization} />);
    
    const container = screen.getByTestId('responsive-container').parentElement;
    expect(container).toHaveClass('h-48', 'w-full');
    
    const outerContainer = container?.parentElement;
    expect(outerContainer).toHaveClass('w-full', 'bg-background', 'border', 'rounded-lg', 'p-2', 'mt-2');
  });

  it('includes required chart components', () => {
    render(<ChatVisualization visualization={baseVisualization} />);
    
    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    expect(screen.getByTestId('legend')).toBeInTheDocument();
  });
});