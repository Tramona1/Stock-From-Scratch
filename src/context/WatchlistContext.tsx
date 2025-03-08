"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useUser } from "@clerk/nextjs"
import { toast } from "@/components/ui/use-toast"

// Define the watchlist item type
export interface WatchlistItem {
  id: string | number
  symbol: string
  price: number
  change: number
  volume: string
  watching: boolean
}

// Define the context type
interface WatchlistContextType {
  watchlist: WatchlistItem[]
  isLoading: boolean
  isAdding: boolean
  error: string | null
  fetchWatchlist: () => Promise<void>
  addToWatchlist: (ticker: string) => Promise<void>
  removeFromWatchlist: (ticker: string) => Promise<void>
  refreshWatchlist: () => Promise<void>
}

// Create the context with a default value
const WatchlistContext = createContext<WatchlistContextType>({
  watchlist: [],
  isLoading: false,
  isAdding: false,
  error: null,
  fetchWatchlist: async () => {},
  addToWatchlist: async () => {},
  removeFromWatchlist: async () => {},
  refreshWatchlist: async () => {},
})

// Custom hook to use the watchlist context
export const useWatchlist = () => useContext(WatchlistContext)

export function WatchlistProvider({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn, user } = useUser()
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch watchlist from API
  const fetchWatchlist = useCallback(async () => {
    if (!isLoaded || !isSignedIn) {
      setWatchlist([])
      setIsLoading(false)
      return
    }
    
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch('/api/watchlist', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch watchlist')
      }
      
      const data = await response.json()
      console.log('Watchlist data:', data)
      
      setWatchlist(data.watchlist || [])
    } catch (err: any) {
      console.error('Error fetching watchlist:', err)
      setError('Failed to load your watchlist')
    } finally {
      setIsLoading(false)
    }
  }, [isLoaded, isSignedIn])

  // Add ticker to watchlist
  const addToWatchlist = async (ticker: string) => {
    if (!ticker) return
    
    const formattedTicker = ticker.toUpperCase()
    if (watchlist.some((item) => item.symbol === formattedTicker)) {
      toast({
        title: "Already in watchlist",
        description: `${formattedTicker} is already in your watchlist`,
      })
      return
    }

    try {
      setIsAdding(true)
      
      const response = await fetch('/api/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ticker: formattedTicker })
      })
      
      const data = await response.json()
      console.log('Add ticker response:', data)
      
      if (!response.ok || !data.success) {
        throw new Error(data.error || data.message || 'Failed to add ticker')
      }
      
      setWatchlist(data.watchlist || [])
      
      toast({
        title: "Added to watchlist",
        description: `${formattedTicker} has been added to your watchlist`,
      })
    } catch (err: any) {
      console.error('Error adding to watchlist:', err)
      toast({
        title: "Error",
        description: `Failed to add ${formattedTicker} to watchlist: ${err.message}`,
        variant: "destructive"
      })
    } finally {
      setIsAdding(false)
    }
  }

  // Remove ticker from watchlist
  const removeFromWatchlist = async (ticker: string) => {
    try {
      const response = await fetch(`/api/watchlist?ticker=${ticker}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.message || 'Failed to remove ticker')
      }
      
      const data = await response.json()
      
      setWatchlist(data.watchlist || [])
      
      toast({
        title: "Removed from watchlist",
        description: `${ticker} has been removed from your watchlist`,
      })
    } catch (err: any) {
      console.error('Error removing from watchlist:', err)
      toast({
        title: "Error",
        description: `Failed to remove ${ticker} from watchlist: ${err.message}`,
        variant: "destructive"
      })
    }
  }

  // Refresh watchlist - convenience method
  const refreshWatchlist = async () => {
    await fetchWatchlist()
  }

  // Fetch watchlist when component mounts
  useEffect(() => {
    fetchWatchlist()
  }, [fetchWatchlist])

  return (
    <WatchlistContext.Provider
      value={{
        watchlist,
        isLoading,
        isAdding,
        error,
        fetchWatchlist,
        addToWatchlist,
        removeFromWatchlist,
        refreshWatchlist,
      }}
    >
      {children}
    </WatchlistContext.Provider>
  )
} 