"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ErrorState } from "@/components/ui/error-state"
import { ArrowUp, ArrowDown } from "lucide-react"

// Define the indicator type
interface MarketIndicator {
  id: number
  name: string
  value: string
  change: string
  trending: string
}

// Mock data
const mockIndicators: MarketIndicator[] = [
  { id: 1, name: "S&P 500", value: "4,892.36", change: "0.82%", trending: "up" },
  { id: 2, name: "Dow Jones", value: "38,762.20", change: "0.32%", trending: "up" },
  { id: 3, name: "NASDAQ", value: "15,756.01", change: "1.14%", trending: "up" },
  { id: 4, name: "Russell 2000", value: "2,064.74", change: "-0.24%", trending: "down" },
  { id: 5, name: "VIX", value: "13.41", change: "-2.33%", trending: "down" },
]

export function MarketIndicators() {
  const [indicators, setIndicators] = useState<MarketIndicator[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIndicators = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // For demo purposes only
      setTimeout(() => {
        setIndicators(mockIndicators)
        setIsLoading(false)
      }, 500)
    } catch (err) {
      console.error('Error fetching indicators:', err)
      setError('Failed to load market indicators')
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchIndicators()
  }, [])

  if (error) {
    return (
      <ErrorState 
        title="Failed to load market indicators" 
        description="We couldn't fetch the latest market data. Please try again later."
        onAction={fetchIndicators}
        actionText="Try Again"
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Indicators</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="grid grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i}>
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                  <div className="h-6 bg-gray-200 rounded w-16 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-12"></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-5 gap-4">
            {indicators.map((indicator) => (
              <div key={indicator.id}>
                <p className="text-sm text-muted-foreground">{indicator.name}</p>
                <p className="text-xl font-bold">{indicator.value}</p>
                <div className="flex items-center">
                  {indicator.trending === 'up' ? (
                    <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
                  ) : (
                    <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
                  )}
                  <span className={indicator.trending === 'up' ? 'text-green-500' : 'text-red-500'}>
                    {indicator.change}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
} 