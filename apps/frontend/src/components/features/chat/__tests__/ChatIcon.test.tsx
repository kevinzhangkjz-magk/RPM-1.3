import { render, screen, fireEvent } from '@testing-library/react';
import { ChatIcon } from '../ChatIcon';
import { useChatStore } from '@/lib/stores/chatStore';

// Mock the store
jest.mock('@/lib/stores/chatStore');
const mockUseChatStore = useChatStore as jest.MockedFunction<typeof useChatStore>;

describe('ChatIcon', () => {
  const mockToggleChat = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseChatStore.mockReturnValue({
      isOpen: false,
      toggleChat: mockToggleChat,
      closeChat: jest.fn(),
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });
  });

  it('renders the chat icon button', () => {
    render(<ChatIcon />);
    
    const button = screen.getByRole('button', { name: /open chat/i });
    expect(button).toBeInTheDocument();
  });

  it('calls toggleChat when clicked', () => {
    render(<ChatIcon />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(mockToggleChat).toHaveBeenCalledTimes(1);
  });

  it('shows correct aria-label when chat is closed', () => {
    render(<ChatIcon />);
    
    const button = screen.getByRole('button', { name: /open chat/i });
    expect(button).toBeInTheDocument();
  });

  it('shows correct aria-label when chat is open', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: mockToggleChat,
      closeChat: jest.fn(),
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatIcon />);
    
    const button = screen.getByRole('button', { name: /close chat/i });
    expect(button).toBeInTheDocument();
  });

  it('applies correct styling when chat is open', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: mockToggleChat,
      closeChat: jest.fn(),
      openChat: jest.fn(),
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      setLoading: jest.fn(),
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });

    render(<ChatIcon />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('scale-95');
  });
});