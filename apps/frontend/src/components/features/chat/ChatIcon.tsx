'use client';

import { MessageCircle } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chatStore';
import { Button } from '@/components/ui/button';

export function ChatIcon() {
  const { isOpen, toggleChat } = useChatStore();

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <Button
        onClick={toggleChat}
        size="lg"
        className={`
          h-14 w-14 rounded-full shadow-lg transition-all duration-200 ease-in-out
          ${isOpen 
            ? 'bg-primary/90 hover:bg-primary scale-95' 
            : 'bg-primary hover:bg-primary/90 hover:scale-110'
          }
        `}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        <MessageCircle 
          className={`h-6 w-6 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : 'rotate-0'
          }`} 
        />
      </Button>
    </div>
  );
}