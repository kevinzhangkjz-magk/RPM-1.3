'use client';

import { 
  ResponsiveContainer, 
  ComposedChart, 
  BarChart, 
  Bar, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend
} from 'recharts';
import { ChatVisualization as ChatVisualizationType } from '@/types/chat';

interface ChatVisualizationProps {
  visualization: ChatVisualizationType;
}

export function ChatVisualization({ visualization }: ChatVisualizationProps) {
  const { chart_type, data, columns } = visualization;

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-xs text-muted-foreground p-2 bg-muted/50 rounded">
        No visualization data available
      </div>
    );
  }

  const renderChart = () => {
    switch (chart_type) {
      case 'scatter':
        return (
          <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey={columns[0]} 
              type="number" 
              domain={['dataMin', 'dataMax']}
              fontSize={10}
            />
            <YAxis fontSize={10} />
            <Tooltip 
              labelStyle={{ fontSize: '10px' }}
              contentStyle={{ fontSize: '10px' }}
            />
            <Legend wrapperStyle={{ fontSize: '10px' }} />
            <Scatter 
              dataKey={columns[1]} 
              fill="#3b82f6" 
              name={columns[1]}
            />
          </ComposedChart>
        );

      case 'multi-scatter':
        return (
          <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey={columns[0]} 
              type="number" 
              domain={['dataMin', 'dataMax']}
              fontSize={10}
            />
            <YAxis fontSize={10} />
            <Tooltip 
              labelStyle={{ fontSize: '10px' }}
              contentStyle={{ fontSize: '10px' }}
            />
            <Legend wrapperStyle={{ fontSize: '10px' }} />
            {columns.slice(1).map((column, index) => (
              <Scatter 
                key={column}
                dataKey={column} 
                fill={index === 0 ? '#3b82f6' : index === 1 ? '#6b7280' : '#ef4444'} 
                name={column}
              />
            ))}
          </ComposedChart>
        );

      case 'bar':
        return (
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey={columns[0]} 
              fontSize={10}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis fontSize={10} />
            <Tooltip 
              labelStyle={{ fontSize: '10px' }}
              contentStyle={{ fontSize: '10px' }}
            />
            <Legend wrapperStyle={{ fontSize: '10px' }} />
            {columns.slice(1).map((column, index) => (
              <Bar 
                key={column}
                dataKey={column} 
                fill={index === 0 ? '#3b82f6' : index === 1 ? '#6b7280' : '#ef4444'} 
                name={column}
              />
            ))}
          </BarChart>
        );

      default:
        return (
          <div className="text-xs text-muted-foreground p-2 bg-muted/50 rounded">
            Unsupported chart type: {chart_type}
          </div>
        );
    }
  };

  return (
    <div className="w-full bg-background border rounded-lg p-2 mt-2">
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}