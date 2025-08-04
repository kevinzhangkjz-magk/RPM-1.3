'use client';

import { User, Bot, Loader2 } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import { ChatVisualization } from './ChatVisualization';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
        {/* Avatar */}
        <div className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser ? 'bg-primary ml-2' : 'bg-muted mr-2'}
        `}>
          {isUser ? (
            <User className="w-4 h-4 text-primary-foreground" />
          ) : (
            <Bot className="w-4 h-4 text-muted-foreground" />
          )}
        </div>

        {/* Message Content */}
        <div className={`
          rounded-lg px-3 py-2 max-w-full
          ${isUser 
            ? 'bg-primary text-primary-foreground' 
            : 'bg-muted text-muted-foreground'
          }
        `}>
          {message.isLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          ) : (
            <>
              <div className="text-sm whitespace-pre-wrap break-words">
                {message.content}
              </div>
              
              {/* Render visualization if present */}
              {!isUser && message.data?.visualization && (
                <div className="mt-3">
                  <ChatVisualization 
                    visualization={message.data.visualization} 
                  />
                </div>
              )}
            </>
          )}
          
          {/* Timestamp */}
          {!message.isLoading && (
            <div className={`
              text-xs mt-1 opacity-70
              ${isUser ? 'text-primary-foreground/70' : 'text-muted-foreground/70'}
            `}>
              {message.timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}