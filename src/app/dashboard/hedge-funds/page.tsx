"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useWatchlist } from "@/context/WatchlistContext"
import { Loader2, AlertTriangle } from "lucide-react"
import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"

// Mock hedge fund data - in a real app, this would come from an API
interface HedgeFundActivity {
  id: string
  fund: string
  ticker: string
  action: "Buy" | "Sell" | "Increase" | "Decrease"
  shares: number
  value: number
  date: string
}

// This would be an API call in a real app
const fetchHedgeFundData = async (): Promise<HedgeFundActivity[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // Return mock data
  return [
    { 
      id: "1", 
      fund: "Renaissance Technologies", 
      ticker: "AAPL", 
      action: "Buy", 
      shares: 1200000, 
      value: 220000000, 
      date: "2024-03-15" 
    },
    { 
      id: "2", 
      fund: "Bridgewater Associates", 
      ticker: "MSFT", 
      action: "Increase", 
      shares: 500000, 
      value: 195000000, 
      date: "2024-03-14" 
    },
    { 
      id: "3", 
      fund: "Citadel", 
      ticker: "TSLA", 
      action: "Decrease", 
      shares: 300000, 
      value: 68000000, 
      date: "2024-03-12" 
    },
    { 
      id: "4", 
      fund: "D.E. Shaw", 
      ticker: "NVDA", 
      action: "Buy", 
      shares: 800000, 
      value: 310000000, 
      date: "2024-03-10" 
    },
    { 
      id: "5", 
      fund: "Two Sigma", 
      ticker: "AMZN", 
      action: "Sell", 
      shares: 150000, 
      value: 25000000, 
      date: "2024-03-08" 
    },
    { 
      id: "6", 
      fund: "Point72", 
      ticker: "META", 
      action: "Increase", 
      shares: 450000, 
      value: 180000000, 
      date: "2024-03-05" 
    },
    { 
      id: "7", 
      fund: "Tiger Global", 
      ticker: "GOOGL", 
      action: "Buy", 
      shares: 350000, 
      value: 520000000, 
      date: "2024-03-03" 
    },
    { 
      id: "8", 
      fund: "Millennium Management", 
      ticker: "AMD", 
      action: "Decrease", 
      shares: 200000, 
      value: 45000000, 
      date: "2024-03-01" 
    }
  ]
}

export default function HedgeFundsPage() {
  const { watchlist, isLoading: isWatchlistLoading } = useWatchlist()
  const [hedgeFundData, setHedgeFundData] = useState<HedgeFundActivity[]>([])
  const [filteredData, setFilteredData] = useState<HedgeFundActivity[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch hedge fund data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const data = await fetchHedgeFundData()
        setHedgeFundData(data)
      } catch (error) {
        console.error("Error fetching hedge fund data:", error)
      } finally {
        setIsLoading(false)
      }
    }

    // Only fetch data if the watchlist has items
    if (watchlist.length > 0) {
      fetchData()
    } else {
      setIsLoading(false)
      setHedgeFundData([])
      setFilteredData([])
    }
  }, [watchlist])

  // Filter data based on watchlist
  useEffect(() => {
    if (watchlist.length > 0) {
      const watchlistSymbols = watchlist.map(item => item.symbol)
      const filtered = hedgeFundData.filter(item => watchlistSymbols.includes(item.ticker))
      setFilteredData(filtered)
    } else {
      setFilteredData([])
    }
  }, [hedgeFundData, watchlist])

  // Format date to a more readable format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format large numbers (like millions)
  const formatValue = (value: number) => {
    if (value >= 1000000000) {
      return `$${(value / 1000000000).toFixed(1)}B`
    }
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    return `$${(value / 1000).toFixed(1)}K`
  }

  // Format shares amount
  const formatShares = (shares: number) => {
    if (shares >= 1000000) {
      return `${(shares / 1000000).toFixed(1)}M shares`
    }
    if (shares >= 1000) {
      return `${(shares / 1000).toFixed(1)}K shares`
    }
    return `${shares} shares`
  }
  
  // Get badge style based on action type
  const getActionBadge = (action: HedgeFundActivity['action']) => {
    switch (action) {
      case 'Buy':
      case 'Increase':
        return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">{action}</Badge>
      case 'Sell':
      case 'Decrease':
        return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100">{action}</Badge>
      default:
        return <Badge>{action}</Badge>
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Hedge Funds</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Hedge Fund Activity</CardTitle>
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
                Add stocks to your watchlist to see hedge fund activity for those stocks.
              </p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hedge fund activity found.</p>
              <p className="text-muted-foreground text-sm mt-1">
                There's no recent hedge fund activity for your watchlist stocks.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b">
                    <th className="pb-2">Date</th>
                    <th className="pb-2">Fund</th>
                    <th className="pb-2">Ticker</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2">Position</th>
                    <th className="pb-2">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredData.map((activity) => (
                    <tr key={activity.id} className="hover:bg-muted/50">
                      <td className="py-3">{formatDate(activity.date)}</td>
                      <td className="py-3 font-medium">{activity.fund}</td>
                      <td className="py-3">{activity.ticker}</td>
                      <td className="py-3">{getActionBadge(activity.action)}</td>
                      <td className="py-3">{formatShares(activity.shares)}</td>
                      <td className="py-3">{formatValue(activity.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Hedge Fund Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {watchlist.length === 0 ? (
            <p className="text-sm text-muted-foreground">Add stocks to your watchlist to see which hedge funds own them.</p>
          ) : (
            <p className="text-sm text-muted-foreground">This section will display the top hedge funds that own the stocks in your watchlist.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 