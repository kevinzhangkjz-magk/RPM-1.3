export interface ChatMessage {
  id: string;
  content: string;
  timestamp: Date;
  type: 'user' | 'ai';
  isLoading?: boolean;
  data?: {
    visualization?: ChatVisualization;
  };
}

export interface ChatVisualization {
  chart_type: 'scatter' | 'bar' | 'multi-scatter';
  data: unknown;
  columns: string[];
}

export interface AIQueryRequest {
  query: string;
}

export interface AIQueryResponse {
  summary: string;
  data?: unknown;
  chart_type?: 'scatter' | 'bar' | 'multi-scatter';
  columns?: string[];
}

export interface ChatState {
  isOpen: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
}