"use client"

import React, { createContext, useContext, useEffect } from 'react'

// Mock market data
const mockMarketData = {
  indicators: [
    { id: 1, name: 'S&P 500', value: '4,782.82', change: '+0.57%', trending: 'up' },
    { id: 2, name: 'Dow Jones', value: '38,654.42', change: '+0.35%', trending: 'up' },
    { id: 3, name: 'NASDAQ', value: '16,745.30', change: '-0.28%', trending: 'down' },
    { id: 4, name: 'Russell 2000', value: '2,089.35', change: '+1.12%', trending: 'up' },
    { id: 5, name: 'VIX', value: '12.80', change: '-3.25%', trending: 'down' }
  ],
  stocks: [
    { id: 1, symbol: 'AAPL', name: 'Apple Inc.', price: 182.63, change: '+1.23%', volume: '58.3M' },
    { id: 2, symbol: 'MSFT', name: 'Microsoft Corp.', price: 402.12, change: '+0.87%', volume: '22.1M' },
    { id: 3, symbol: 'GOOGL', name: 'Alphabet Inc.', price: 142.56, change: '-0.45%', volume: '18.7M' },
    { id: 4, symbol: 'AMZN', name: 'Amazon.com Inc.', price: 175.35, change: '+2.10%', volume: '35.2M' },
    { id: 5, symbol: 'NVDA', name: 'NVIDIA Corp.', price: 816.20, change: '+3.45%', volume: '42.8M' }
  ],
  news: [
    { id: 1, title: 'Fed Signals Rate Cut by September', source: 'Financial Times', time: '2h ago' },
    { id: 2, title: 'Tech Rally Continues as AI Optimism Grows', source: 'Wall Street Journal', time: '3h ago' },
    { id: 3, title: 'Oil Prices Drop Amid Supply Concerns', source: 'Bloomberg', time: '5h ago' },
    { id: 4, title: 'Inflation Data Shows Cooling Trend', source: 'CNBC', time: '8h ago' }
  ],
  alerts: [
    { id: 1, title: 'AAPL just crossed above its 200-day moving average', priority: 'high', time: 'Just now' },
    { id: 2, title: 'VIX is down 15% this week - market sentiment is bullish', priority: 'medium', time: '1h ago' },
    { id: 3, title: 'NVDA options volume surging ahead of earnings', priority: 'high', time: '2h ago' }
  ]
}

// Create context
const MockDataContext = createContext(mockMarketData)

// Hook to use the mock data
export const useMockData = () => useContext(MockDataContext)

// Provider component
export function MockDataProvider({ children }: { children: React.ReactNode }) {
  // Intercept API calls and override with mock data
  useEffect(() => {
    // Save the original fetch
    const originalFetch = window.fetch
    
    // Override fetch to intercept API calls
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString()
      
      // If it's a market data API call, return mock data
      if (url.includes('/api/market') || url.includes('/api/stocks') || url.includes('/api/indicators')) {
        console.log('Intercepted API call to:', url)
        return new Response(JSON.stringify({ 
          success: true, 
          data: 
            url.includes('indicators') ? mockMarketData.indicators :
            url.includes('stocks') ? mockMarketData.stocks :
            url.includes('news') ? mockMarketData.news :
            url.includes('alerts') ? mockMarketData.alerts :
            mockMarketData
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      }
      
      // Otherwise, use the original fetch
      return originalFetch(input, init)
    }
    
    // Clean up
    return () => {
      window.fetch = originalFetch
    }
  }, [])
  
  return (
    <MockDataContext.Provider value={mockMarketData}>
      {children}
    </MockDataContext.Provider>
  )
} 