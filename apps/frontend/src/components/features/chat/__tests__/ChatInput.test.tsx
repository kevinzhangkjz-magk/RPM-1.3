import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatInput } from '../ChatInput';
import { useChatStore } from '@/lib/stores/chatStore';
import { sitesApi } from '@/lib/api/sites';

// Mock the store
jest.mock('@/lib/stores/chatStore');
const mockUseChatStore = useChatStore as jest.MockedFunction<typeof useChatStore>;

// Mock the API
const mockQueryAI = jest.fn();
jest.mock('@/lib/api/sites', () => ({
  sitesApi: {
    queryAI: mockQueryAI,
  },
}));

describe('ChatInput', () => {
  const mockAddMessage = jest.fn().mockReturnValue('msg-123');
  const mockUpdateMessage = jest.fn();
  const mockSetLoading = jest.fn();

  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Reset the mock functions
    mockQueryAI.mockReset();

    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: jest.fn(),
      openChat: jest.fn(),
      addMessage: mockAddMessage,
      updateMessage: mockUpdateMessage,
      setLoading: mockSetLoading,
      clearMessages: jest.fn(),
      messages: [],
      isLoading: false,
    });
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('renders textarea and send button', () => {
    renderWithQueryClient(<ChatInput />);
    
    expect(screen.getByPlaceholderText('Ask about your solar sites...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '' })).toBeInTheDocument();
  });

  it('updates input value when typing', () => {
    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    fireEvent.change(textarea, { target: { value: 'Test message' } });
    
    expect(textarea).toHaveValue('Test message');
  });

  it('shows character counter', () => {
    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    fireEvent.change(textarea, { target: { value: 'Test' } });
    
    expect(screen.getByText('4/1000')).toBeInTheDocument();
  });

  it('submits message on form submit', async () => {
    mockQueryAI.mockResolvedValue({
      summary: 'AI response',
    });

    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const form = textarea.closest('form')!;
    
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.submit(form);
    
    expect(mockAddMessage).toHaveBeenCalledWith('Test question', 'user');
    await waitFor(() => {
      expect(mockQueryAI).toHaveBeenCalledWith({ query: 'Test question' });
    });
  });

  it('submits message on Enter key (without shift)', () => {
    mockQueryAI.mockResolvedValue({
      summary: 'AI response',
    });

    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    
    expect(mockAddMessage).toHaveBeenCalledWith('Test question', 'user');
  });

  it('does not submit on Enter with shift key', () => {
    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    
    expect(mockAddMessage).not.toHaveBeenCalled();
  });

  it('prevents submission of empty messages', () => {
    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const form = textarea.closest('form')!;
    
    fireEvent.change(textarea, { target: { value: '   ' } });
    fireEvent.submit(form);
    
    expect(mockAddMessage).not.toHaveBeenCalled();
  });

  it('prevents submission of messages over 1000 characters', () => {
    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const form = textarea.closest('form')!;
    const longMessage = 'a'.repeat(1001);
    
    fireEvent.change(textarea, { target: { value: longMessage } });
    fireEvent.submit(form);
    
    expect(mockAddMessage).toHaveBeenCalledWith(
      'Sorry, your message is too long. Please keep it under 1000 characters.',
      'ai'
    );
    expect(mockQueryAI).not.toHaveBeenCalled();
  });

  it('handles API success with visualization data', async () => {
    const mockResponse = {
      summary: 'Here is the analysis',
      data: [{ x: 1, y: 2 }],
      chart_type: 'scatter' as const,
      columns: ['x', 'y'],
    };
    
    mockQueryAI.mockResolvedValue(mockResponse);

    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const form = textarea.closest('form')!;
    
    fireEvent.change(textarea, { target: { value: 'Show me data' } });
    fireEvent.submit(form);
    
    await waitFor(() => {
      expect(mockUpdateMessage).toHaveBeenCalled();
    });
  });

  it('handles API errors', async () => {
    mockQueryAI.mockRejectedValue(new Error('API Error'));

    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const form = textarea.closest('form')!;
    
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.submit(form);
    
    await waitFor(() => {
      expect(mockAddMessage).toHaveBeenCalledWith(
        'Sorry, I encountered an error: API Error',
        'ai'
      );
    });
  });

  it('disables input and button when loading', () => {
    mockUseChatStore.mockReturnValue({
      isOpen: true,
      toggleChat: jest.fn(),
      closeChat: jest.fn(),
      openChat: jest.fn(),
      addMessage: mockAddMessage,
      updateMessage: mockUpdateMessage,
      setLoading: mockSetLoading,
      clearMessages: jest.fn(),
      messages: [],
      isLoading: true,
    });

    renderWithQueryClient(<ChatInput />);
    
    const textarea = screen.getByPlaceholderText('Ask about your solar sites...');
    const button = screen.getByRole('button');
    
    expect(textarea).toBeDisabled();
    expect(button).toBeDisabled();
  });
});