import { create } from 'zustand';
import { ChatMessage, ChatState } from '@/types/chat';

interface ChatStore extends ChatState {
  toggleChat: () => void;
  closeChat: () => void;
  openChat: () => void;
  addMessage: (content: string, type: 'user' | 'ai') => string;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  isOpen: false,
  messages: [],
  isLoading: false,

  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  
  closeChat: () => set({ isOpen: false }),
  
  openChat: () => set({ isOpen: true }),

  addMessage: (content: string, type: 'user' | 'ai') => {
    const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const message: ChatMessage = {
      id,
      content,
      type,
      timestamp: new Date(),
      isLoading: type === 'ai'
    };

    set((state) => ({
      messages: [...state.messages, message]
    }));

    return id;
  },

  updateMessage: (id: string, updates: Partial<ChatMessage>) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      )
    }));
  },

  setLoading: (loading: boolean) => set({ isLoading: loading }),

  clearMessages: () => set({ messages: [] })
}));