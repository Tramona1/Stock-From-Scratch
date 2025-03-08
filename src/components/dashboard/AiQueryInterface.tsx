"use client"

import { useState, useRef, useEffect } from 'react'
import { useWatchlist } from '@/context/WatchlistContext'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Send, Bot, User, Loader2, AlertCircle, ExternalLink } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { toast } from "@/components/ui/use-toast"

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface QueryResponse {
  answer: string
  sources: {
    type: string
    count: number
  }[]
}

interface DataSourceBadgeProps {
  type: string;
  count: number;
}

const DataSourceBadge = ({ type, count }: DataSourceBadgeProps) => {
  // Skip no_data sources
  if (type === 'no_data' || count === 0) return null;
  
  // Map data types to friendly names
  const typeNames: Record<string, string> = {
    'insider_trades': 'Insider Trades',
    'analyst_ratings': 'Analyst Ratings',
    'options_flow': 'Options Flow',
    'economic_calendar_events': 'Economic Calendar',
    'fda_calendar_events': 'FDA Calendar',
    'political_trades': 'Political Trades',
    'dark_pool_data': 'Dark Pool Data',
    'financial_news': 'Financial News'
  };
  
  const displayName = typeNames[type] || type;
  
  return (
    <Badge variant="outline" className="mr-1 mb-1">
      {displayName}: {count}
    </Badge>
  );
};

export function AiQueryInterface() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sources, setSources] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { watchlist } = useWatchlist()

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setSources([])

    try {
      // Extract watchlist symbols for context
      const watchlistSymbols = watchlist.map(item => item.symbol)
      
      const response = await fetch('/api/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          watchlistSymbols,
          history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to get response: ${response.statusText}`)
      }

      const data: QueryResponse = await response.json()
      
      // Add AI response
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
      setSources(data.sources || [])
    } catch (error) {
      console.error('Error querying AI:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
      toast({
        title: "Error",
        description: `Failed to get AI response: ${(error as Error).message}`,
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-xl flex items-center">
          <Bot className="mr-2 h-5 w-5" />
          Financial AI Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto mb-4">
          {messages.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground">
              <Bot size={48} className="mx-auto mb-4 opacity-50" />
              <p className="font-medium">Ask me anything about your watchlist stocks</p>
              <p className="text-sm mt-2">
                Try questions like "Show me recent insider trades for AAPL" or
                "What were the latest analyst ratings for my watchlist stocks?"
              </p>
              
              {watchlist.length === 0 && (
                <div className="mt-6 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-md p-3 text-amber-800 dark:text-amber-300 text-sm">
                  <AlertCircle className="inline-block mr-2 h-4 w-4" />
                  <span>You don't have any stocks in your watchlist. Add stocks to your watchlist to get personalized insights.</span>
                </div>
              )}
              
              <div className="mt-6 grid gap-2 md:grid-cols-2">
                <Button 
                  variant="outline" 
                  onClick={() => setInput("Show me recent insider trades for my watchlist stocks")}
                  className="justify-start text-left font-normal text-sm"
                >
                  Show me recent insider trades
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setInput("What are the latest analyst ratings for AAPL?")}
                  className="justify-start text-left font-normal text-sm"
                >
                  Latest analyst ratings for AAPL
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setInput("Tell me about upcoming FDA events for biotech stocks")}
                  className="justify-start text-left font-normal text-sm"
                >
                  Upcoming FDA events
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setInput("Explain recent options activity in my watchlist")}
                  className="justify-start text-left font-normal text-sm"
                >
                  Recent options activity
                </Button>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`mb-4 flex ${
                  message.role === 'assistant' ? 'justify-start' : 'justify-end'
                }`}
              >
                <div
                  className={`rounded-lg px-4 py-2 max-w-[80%] ${
                    message.role === 'assistant'
                      ? 'bg-secondary text-secondary-foreground'
                      : 'bg-primary text-primary-foreground'
                  }`}
                >
                  <div className="flex items-center mb-1">
                    {message.role === 'assistant' ? (
                      <Bot className="h-4 w-4 mr-2" />
                    ) : (
                      <User className="h-4 w-4 mr-2" />
                    )}
                    <span className="text-xs">
                      {message.role === 'assistant' ? 'AI Assistant' : 'You'}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="mb-4 flex justify-start">
              <div className="rounded-lg px-4 py-2 bg-secondary text-secondary-foreground">
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  <span className="text-xs">AI Assistant is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Display data sources if available */}
          {sources && sources.length > 0 && messages.length > 0 && !isLoading && (
            <div className="flex flex-wrap mb-4 mt-2">
              <span className="text-xs text-muted-foreground mr-2 mt-1">Sources:</span>
              {sources.map((source, index) => (
                <DataSourceBadge key={index} type={source.type} count={source.count} />
              ))}
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t pt-4">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex space-x-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your watchlist stocks..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
} 