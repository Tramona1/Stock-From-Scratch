"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useWatchlist } from "@/context/WatchlistContext"
import { Loader2, AlertTriangle } from "lucide-react"
import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"

// Mock options flow data - in a real app, this would come from an API
interface OptionsFlowItem {
  id: string
  ticker: string
  strike: number
  expiration: string
  type: "CALL" | "PUT"
  premium: number
  volume: number
  openInterest: number
  sentiment: "Bullish" | "Bearish" | "Neutral"
  date: string
}

// This would be an API call in a real app
const fetchOptionsFlowData = async (): Promise<OptionsFlowItem[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // Return mock data
  return [
    { 
      id: "1", 
      ticker: "AAPL", 
      strike: 190,
      expiration: "2023-06-16",
      type: "CALL", 
      premium: 4500000, 
      volume: 12000,
      openInterest: 25000,
      sentiment: "Bullish",
      date: "2023-05-15" 
    },
    { 
      id: "2", 
      ticker: "TSLA", 
      strike: 200,
      expiration: "2023-06-23",
      type: "PUT", 
      premium: 5200000, 
      volume: 8000,
      openInterest: 15000,
      sentiment: "Bearish",
      date: "2023-05-14" 
    },
    { 
      id: "3", 
      ticker: "NVDA", 
      strike: 500,
      expiration: "2023-07-21",
      type: "CALL", 
      premium: 7800000, 
      volume: 15000,
      openInterest: 30000,
      sentiment: "Bullish",
      date: "2023-05-12" 
    },
    { 
      id: "4", 
      ticker: "META", 
      strike: 300,
      expiration: "2023-06-30",
      type: "CALL", 
      premium: 3200000, 
      volume: 6000,
      openInterest: 12000,
      sentiment: "Bullish",
      date: "2023-05-10" 
    },
    { 
      id: "5", 
      ticker: "MSFT", 
      strike: 350,
      expiration: "2023-06-16",
      type: "PUT", 
      premium: 2800000, 
      volume: 5000,
      openInterest: 9000,
      sentiment: "Bearish",
      date: "2023-05-09" 
    },
    { 
      id: "6", 
      ticker: "AMZN", 
      strike: 120,
      expiration: "2023-07-14",
      type: "CALL", 
      premium: 4100000, 
      volume: 9000,
      openInterest: 18000,
      sentiment: "Bullish",
      date: "2023-05-08" 
    }
  ]
}

export default function OptionsFlowPage() {
  const { watchlist, isLoading: isWatchlistLoading } = useWatchlist()
  const [optionsData, setOptionsData] = useState<OptionsFlowItem[]>([])
  const [filteredData, setFilteredData] = useState<OptionsFlowItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch options flow data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const data = await fetchOptionsFlowData()
        setOptionsData(data)
      } catch (error) {
        console.error("Error fetching options flow data:", error)
      } finally {
        setIsLoading(false)
      }
    }

    // Only fetch data if the watchlist has items
    if (watchlist.length > 0) {
      fetchData()
    } else {
      setIsLoading(false)
      setOptionsData([])
      setFilteredData([])
    }
  }, [watchlist])

  // Filter data based on watchlist
  useEffect(() => {
    if (watchlist.length > 0) {
      const watchlistSymbols = watchlist.map(item => item.symbol)
      const filtered = optionsData.filter(item => watchlistSymbols.includes(item.ticker))
      setFilteredData(filtered)
    } else {
      setFilteredData([])
    }
  }, [optionsData, watchlist])

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format expiration date
  const formatExpiration = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format premium
  const formatPremium = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    return `$${(value / 1000).toFixed(0)}K`
  }

  // Format volume with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Options Flow</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Unusual Options Activity</CardTitle>
          <CardDescription>
            Track significant options trades that may indicate institutional sentiment or upcoming catalysts.
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
                Add stocks to your watchlist to see options activity for those stocks.
              </p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No options activity found.</p>
              <p className="text-muted-foreground text-sm mt-1">
                There's no recent options activity for your watchlist stocks.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {filteredData.map((option) => (
                <div 
                  key={option.id} 
                  className="border-b pb-4 last:border-b-0 last:pb-0"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">{option.ticker}</span>
                        <Badge className={option.type === 'CALL' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'}>
                          {option.type}
                        </Badge>
                        <Badge className={
                          option.sentiment === 'Bullish' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' 
                            : option.sentiment === 'Bearish' 
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                        }>
                          {option.sentiment}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ${option.strike} strike, expires {formatExpiration(option.expiration)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatDate(option.date)}</div>
                      <div className="text-sm text-muted-foreground">Premium: {formatPremium(option.premium)}</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div>
                      <p className="text-sm text-muted-foreground">Volume</p>
                      <p>{formatNumber(option.volume)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Open Interest</p>
                      <p>{formatNumber(option.openInterest)}</p>
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