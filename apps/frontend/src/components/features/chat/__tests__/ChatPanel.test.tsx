import { render, screen, fireEvent } from '@testing-library/react';
import { ChatPanel } from '../ChatPanel';
import { useChatStore } from '@/lib/stores/chatStore';

// Mock the store
jest.mock('@/lib/stores/chatStore');
const mockUseChatStore = useChatStore as jest.MockedFunction<typeof useChatStore>;

// Mock child components
jest.mock('../ChatInput', () => ({
  ChatInput: () => <div data-testid="chat-input">ChatInput</div>
}));

jest.mock('../ChatMessage', () => ({
  ChatMessage: ({ message }: { message: { content: string } }) => (
    <div data-testid="chat-message">{message.content}</div>
  )
}));

describe('ChatPanel', () => {
  const mockCloseChat = jest.fn();
  const mockMessages = [
    {
      id: '1',
      content: 'Hello',
      type: 'user' as const,
      timestamp: new Date(),
      isLoading: false,
    },
    {
      id: '2',
      content: 'Hi there!',
      type: 'ai' as const,
      timestamp: new Date(),
      isLoading: false,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = jest.fn();
  });

  it('does not render when chat is closed', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: false,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatPanel />);
    
    expect(screen.queryByText('AI Assistant')).not.toBeInTheDocument();
  });

  it('renders when chat is open', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatPanel />);
    
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });

  it('calls closeChat when close button is clicked', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatPanel />);
    
    const closeButton = screen.getByRole('button', { name: /close chat/i });
    fireEvent.click(closeButton);
    
    expect(mockCloseChat).toHaveBeenCalledTimes(1);
  });

  it('shows empty state when no messages', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatPanel />);
    
    expect(screen.getByText('Ask me anything about your solar sites!')).toBeInTheDocument();
    expect(screen.getByText('Try: "Which sites are underperforming?"')).toBeInTheDocument();
  });

  it('renders messages when available', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: mockMessages,
      isLoading: false,
    });

    render(<ChatPanel />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('renders ChatInput component', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: mockCloseChat,
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatPanel />);
    
    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
  });
});