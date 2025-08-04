'use client';

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chatStore';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';

export function ChatPanel() {
  const { isOpen, closeChat, messages } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-24 right-6 z-40">
      <Card className={`
        w-96 h-[500px] shadow-xl border-0 bg-background/95 backdrop-blur-sm
        transform transition-all duration-300 ease-in-out
        ${isOpen ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-4 opacity-0 scale-95'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <h3 className="font-semibold text-sm">AI Assistant</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={closeChat}
            className="h-8 w-8 p-0 hover:bg-muted"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[380px]">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-8">
              <p>Ask me anything about your solar sites!</p>
              <p className="text-xs mt-2">Try: &quot;Which sites are underperforming?&quot;</p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <ChatInput />
        </div>
      </Card>
    </div>
  );
}