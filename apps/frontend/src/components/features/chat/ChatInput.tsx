'use client';

import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { useChatStore } from '../../../lib/stores/chatStore';
import { Button } from '@/components/ui/button';
import { sitesApi } from '../../../lib/api/sites';
import { AIQueryRequest } from '@/types/chat';

export function ChatInput() {
  const [input, setInput] = useState('');
  const { addMessage, updateMessage, isLoading, setLoading } = useChatStore();

  const queryMutation = useMutation({
    mutationFn: (request: AIQueryRequest) => sitesApi.queryAI(request),
    onMutate: () => {
      setLoading(true);
    },
    onSuccess: (response) => {
      // Add AI response message
      const aiMessageId = addMessage(response.summary, 'ai');
      
      // Update the message to include visualization data if present
      if (response.data && response.chart_type && response.columns) {
        updateMessage(aiMessageId, {
          isLoading: false,
          content: response.summary,
        });
        
        // Store visualization data in the message for rendering
        setTimeout(() => {
          updateMessage(aiMessageId, {
            data: {
              visualization: {
                chart_type: response.chart_type!,
                data: response.data,
                columns: response.columns!,
              }
            }
          });
        }, 100);
      } else {
        updateMessage(aiMessageId, {
          isLoading: false,
          content: response.summary,
        });
      }
      
      setLoading(false);
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Something went wrong';
      addMessage(`Sorry, I encountered an error: ${errorMessage}`, 'ai');
      setLoading(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    // Validate input length (1-1000 characters as per API spec)
    if (trimmedInput.length > 1000) {
      addMessage('Sorry, your message is too long. Please keep it under 1000 characters.', 'ai');
      return;
    }

    // Add user message
    addMessage(trimmedInput, 'user');
    
    // Clear input
    setInput('');
    
    // Send to API
    queryMutation.mutate({ query: trimmedInput });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <div className="flex-1">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your solar sites..."
          className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[40px] max-h-[120px]"
          rows={1}
          disabled={isLoading}
          maxLength={1000}
        />
        <div className="text-xs text-muted-foreground mt-1 text-right">
          {input.length}/1000
        </div>
      </div>
      <Button
        type="submit"
        size="sm"
        disabled={!input.trim() || isLoading}
        className="self-start mt-0 h-10 w-10 p-0"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  );
}