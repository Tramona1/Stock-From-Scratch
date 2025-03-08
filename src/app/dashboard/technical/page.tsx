"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useWatchlist } from "@/context/WatchlistContext"
import { Loader2, AlertTriangle } from "lucide-react"
import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"

// Mock technical analysis data - in a real app, this would come from an API
interface TechnicalSignal {
  id: string
  ticker: string
  signal: string
  pattern: string
  timeframe: string
  price: number
  strength: "Strong" | "Moderate" | "Weak"
  date: string
}

// This would be an API call in a real app
const fetchTechnicalData = async (): Promise<TechnicalSignal[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // Return mock data
  return [
    { 
      id: "1", 
      ticker: "AAPL", 
      signal: "Bullish",
      pattern: "Golden Cross",
      timeframe: "Daily", 
      price: 182.50, 
      strength: "Strong",
      date: "2023-05-15" 
    },
    { 
      id: "2", 
      ticker: "MSFT", 
      signal: "Bullish",
      pattern: "Cup and Handle",
      timeframe: "Weekly", 
      price: 330.75, 
      strength: "Moderate",
      date: "2023-05-14" 
    },
    { 
      id: "3", 
      ticker: "TSLA", 
      signal: "Bearish",
      pattern: "Head and Shoulders",
      timeframe: "Daily", 
      price: 205.30, 
      strength: "Strong",
      date: "2023-05-12" 
    },
    { 
      id: "4", 
      ticker: "NVDA", 
      signal: "Bullish",
      pattern: "Breakout",
      timeframe: "Daily", 
      price: 480.25, 
      strength: "Strong",
      date: "2023-05-10" 
    },
    { 
      id: "5", 
      ticker: "META", 
      signal: "Bullish",
      pattern: "Ascending Triangle",
      timeframe: "Daily", 
      price: 290.85, 
      strength: "Moderate",
      date: "2023-05-08" 
    },
    { 
      id: "6", 
      ticker: "AMZN", 
      signal: "Neutral",
      pattern: "Consolidation",
      timeframe: "Daily", 
      price: 122.15, 
      strength: "Weak",
      date: "2023-05-07" 
    }
  ]
}

export default function TechnicalPage() {
  const { watchlist, isLoading: isWatchlistLoading } = useWatchlist()
  const [technicalData, setTechnicalData] = useState<TechnicalSignal[]>([])
  const [filteredData, setFilteredData] = useState<TechnicalSignal[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch technical data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const data = await fetchTechnicalData()
        setTechnicalData(data)
      } catch (error) {
        console.error("Error fetching technical data:", error)
      } finally {
        setIsLoading(false)
      }
    }

    // Only fetch data if the watchlist has items
    if (watchlist.length > 0) {
      fetchData()
    } else {
      setIsLoading(false)
      setTechnicalData([])
      setFilteredData([])
    }
  }, [watchlist])

  // Filter data based on watchlist
  useEffect(() => {
    if (watchlist.length > 0) {
      const watchlistSymbols = watchlist.map(item => item.symbol)
      const filtered = technicalData.filter(item => watchlistSymbols.includes(item.ticker))
      setFilteredData(filtered)
    } else {
      setFilteredData([])
    }
  }, [technicalData, watchlist])

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format price with dollar sign
  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`
  }

  // Get badge style based on signal
  const getSignalBadge = (signal: string) => {
    switch (signal) {
      case 'Bullish':
        return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">Bullish</Badge>
      case 'Bearish':
        return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100">Bearish</Badge>
      default:
        return <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">Neutral</Badge>
    }
  }

  // Get strength indicator
  const getStrengthIndicator = (strength: string) => {
    switch (strength) {
      case 'Strong':
        return (
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
          </div>
        )
      case 'Moderate':
        return (
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-yellow-500 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-gray-300"></div>
          </div>
        )
      default:
        return (
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-gray-400 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-gray-300 mr-1"></div>
            <div className="w-2 h-2 rounded-full bg-gray-300"></div>
          </div>
        )
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Technical Analysis</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Technical Signals</CardTitle>
          <CardDescription>
            Key technical analysis patterns and signals for major stocks.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading || isWatchlistLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : watchlist.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Your watchlist is empty.</p>
              <p className="text-muted-foreground text-sm mt-1">
                Add stocks to your watchlist to see technical signals for those stocks.
              </p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No technical signals found.</p>
              <p className="text-muted-foreground text-sm mt-1">
                There are no recent technical signals for your watchlist stocks.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {filteredData.map((signal) => (
                <div 
                  key={signal.id} 
                  className="border-b pb-4 last:border-b-0 last:pb-0"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">{signal.ticker}</span>
                        {getSignalBadge(signal.signal)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {signal.pattern} on {signal.timeframe} timeframe
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatDate(signal.date)}</div>
                      <div className="text-sm text-muted-foreground">{formatPrice(signal.price)}</div>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center mt-3">
                    <div>
                      <p className="text-sm text-muted-foreground">Signal Strength</p>
                      <p className="font-medium">{signal.strength}</p>
                    </div>
                    <div>
                      {getStrengthIndicator(signal.strength)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 