import { renderHook, act } from '@testing-library/react';
import { useChatStore } from '@/lib/stores/chatStore';

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    act(() => {
      const store = useChatStore.getState();
      store.closeChat();
      store.clearMessages();
      store.setLoading(false);
    });
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useChatStore());
    
    expect(result.current.isOpen).toBe(false);
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('toggles chat state', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.toggleChat();
    });
    
    expect(result.current.isOpen).toBe(true);
    
    act(() => {
      result.current.toggleChat();
    });
    
    expect(result.current.isOpen).toBe(false);
  });

  it('opens and closes chat', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.openChat();
    });
    
    expect(result.current.isOpen).toBe(true);
    
    act(() => {
      result.current.closeChat();
    });
    
    expect(result.current.isOpen).toBe(false);
  });

  it('adds messages correctly', () => {
    const { result } = renderHook(() => useChatStore());
    
    let messageId: string;
    
    act(() => {
      messageId = result.current.addMessage('Hello', 'user');
    });
    
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]).toMatchObject({
      id: messageId!,
      content: 'Hello',
      type: 'user',
      isLoading: false,
    });
    expect(result.current.messages[0].timestamp).toBeInstanceOf(Date);
  });

  it('adds AI messages with loading state', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.addMessage('AI response', 'ai');
    });
    
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]).toMatchObject({
      content: 'AI response',
      type: 'ai',
      isLoading: true,
    });
  });

  it('updates messages correctly', () => {
    const { result } = renderHook(() => useChatStore());
    
    let messageId: string;
    
    act(() => {
      messageId = result.current.addMessage('Original', 'ai');
    });
    
    act(() => {
      result.current.updateMessage(messageId!, {
        content: 'Updated content',
        isLoading: false,
      });
    });
    
    expect(result.current.messages[0]).toMatchObject({
      id: messageId!,
      content: 'Updated content',
      type: 'ai',
      isLoading: false,
    });
  });

  it('does not update non-existent messages', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.addMessage('Test', 'user');
    });
    
    const originalMessage = result.current.messages[0];
    
    act(() => {
      result.current.updateMessage('non-existent-id', {
        content: 'Should not update',
      });
    });
    
    expect(result.current.messages[0]).toEqual(originalMessage);
  });

  it('sets loading state', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.setLoading(true);
    });
    
    expect(result.current.isLoading).toBe(true);
    
    act(() => {
      result.current.setLoading(false);
    });
    
    expect(result.current.isLoading).toBe(false);
  });

  it('clears messages', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.addMessage('Message 1', 'user');
      result.current.addMessage('Message 2', 'ai');
    });
    
    expect(result.current.messages).toHaveLength(2);
    
    act(() => {
      result.current.clearMessages();
    });
    
    expect(result.current.messages).toEqual([]);
  });

  it('generates unique message IDs', () => {
    const { result } = renderHook(() => useChatStore());
    
    let id1: string = '';
    let id2: string = '';
    
    act(() => {
      id1 = result.current.addMessage('Message 1', 'user');
      id2 = result.current.addMessage('Message 2', 'user');
    });
    
    expect(id1).not.toBe(id2);
    expect(id1).toMatch(/^msg-\d+-[a-z0-9]+$/);
    expect(id2).toMatch(/^msg-\d+-[a-z0-9]+$/);
  });

  it('maintains message order', () => {
    const { result } = renderHook(() => useChatStore());
    
    act(() => {
      result.current.addMessage('First', 'user');
      result.current.addMessage('Second', 'ai');
      result.current.addMessage('Third', 'user');
    });
    
    expect(result.current.messages).toHaveLength(3);
    expect(result.current.messages[0].content).toBe('First');
    expect(result.current.messages[1].content).toBe('Second');
    expect(result.current.messages[2].content).toBe('Third');
  });
});