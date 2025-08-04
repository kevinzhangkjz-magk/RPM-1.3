import { render, screen } from '@testing-library/react';
import { ChatMessage } from '../ChatMessage';
import { ChatMessage as ChatMessageType } from '@/types/chat';

// Mock the ChatVisualization component
jest.mock('../ChatVisualization', () => ({
  ChatVisualization: ({ visualization }: { visualization: { chart_type: string } }) => (
    <div data-testid="chat-visualization">
      Chart: {visualization.chart_type}
    </div>
  )
}));

describe('ChatMessage', () => {
  const baseMessage: ChatMessageType = {
    id: '1',
    content: 'Test message',
    timestamp: new Date('2023-01-01T12:00:00Z'),
    type: 'user',
    isLoading: false,
  };

  it('renders user message correctly', () => {
    render(<ChatMessage message={baseMessage} />);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
    // Time format will depend on locale, so just check that timestamp is rendered
    expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
  });

  it('renders AI message correctly', () => {
    const aiMessage: ChatMessageType = {
      ...baseMessage,
      type: 'ai',
    };

    render(<ChatMessage message={aiMessage} />);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
  });

  it('shows loading state for AI messages', () => {
    const loadingMessage: ChatMessageType = {
      ...baseMessage,
      type: 'ai',
      isLoading: true,
    };

    render(<ChatMessage message={loadingMessage} />);
    
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
    expect(screen.queryByText('12:00 PM')).not.toBeInTheDocument();
  });

  it('renders visualization for AI messages with chart data', () => {
    const messageWithVisualization: ChatMessageType = {
      ...baseMessage,
      type: 'ai',
      data: {
        visualization: {
          chart_type: 'scatter',
          data: [{ x: 1, y: 2 }],
          columns: ['x', 'y'],
        }
      }
    };

    render(<ChatMessage message={messageWithVisualization} />);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.getByTestId('chat-visualization')).toBeInTheDocument();
    expect(screen.getByText('Chart: scatter')).toBeInTheDocument();
  });

  it('does not render visualization for user messages', () => {
    const userMessageWithData: ChatMessageType = {
      ...baseMessage,
      type: 'user',
      data: {
        visualization: {
          chart_type: 'scatter',
          data: [{ x: 1, y: 2 }],
          columns: ['x', 'y'],
        }
      }
    };

    render(<ChatMessage message={userMessageWithData} />);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.queryByTestId('chat-visualization')).not.toBeInTheDocument();
  });

  it('applies correct styling for user messages', () => {
    render(<ChatMessage message={baseMessage} />);
    
    const messageContainer = screen.getByText('Test message').parentElement;
    expect(messageContainer).toHaveClass('bg-primary', 'text-primary-foreground');
  });

  it('applies correct styling for AI messages', () => {
    const aiMessage: ChatMessageType = {
      ...baseMessage,
      type: 'ai',
    };

    render(<ChatMessage message={aiMessage} />);
    
    const messageContainer = screen.getByText('Test message').parentElement;
    expect(messageContainer).toHaveClass('bg-muted', 'text-muted-foreground');
  });

  it('preserves whitespace in message content', () => {
    const messageWithWhitespace: ChatMessageType = {
      ...baseMessage,
      content: 'Line 1\nLine 2\n  Indented line',
    };

    render(<ChatMessage message={messageWithWhitespace} />);
    
    const messageElement = screen.getByText(/Line 1/);
    expect(messageElement).toHaveClass('whitespace-pre-wrap');
  });

  it('handles long messages with break-words', () => {
    const longMessage: ChatMessageType = {
      ...baseMessage,
      content: 'verylongwordthatshouldbreakatboundarieswhenneeded',
    };

    render(<ChatMessage message={longMessage} />);
    
    const messageElement = screen.getByText(longMessage.content);
    expect(messageElement).toHaveClass('break-words');
  });
});