"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Zap, AlertTriangle } from "lucide-react"
import { useWatchlist } from "@/context/WatchlistContext"
import { useState } from "react"

interface ScanCardProps {
  title: string
  description: string
  onClick: () => void
  disabled?: boolean
}

function ScanCard({ title, description, onClick, disabled = false }: ScanCardProps) {
  return (
    <div 
      className={`border rounded-md p-4 ${disabled ? 'opacity-60 cursor-not-allowed' : 'hover:bg-muted cursor-pointer'}`} 
      onClick={disabled ? undefined : onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium">{title}</h3>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
        <Zap className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  )
}

export function MarketScanner() {
  const { watchlist, isLoading } = useWatchlist()
  const [scanQuery, setScanQuery] = useState("")
  
  const runScan = (scanType: string) => {
    if (watchlist.length === 0) return
    console.log(`Running ${scanType} scan`)
    // This would trigger the actual scan logic
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Scanner</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-6">
          <Input 
            placeholder="Scan for..." 
            value={scanQuery}
            onChange={(e) => setScanQuery(e.target.value)}
            disabled={watchlist.length === 0 || isLoading}
          />
          <Button disabled={watchlist.length === 0 || isLoading || !scanQuery.trim()}>
            <Search className="h-4 w-4 mr-2" />
            Scan
          </Button>
        </div>
        
        {watchlist.length === 0 && !isLoading ? (
          <div className="text-center p-4 border border-dashed rounded-md">
            <AlertTriangle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm font-medium mb-1">No stocks to scan</p>
            <p className="text-xs text-muted-foreground">
              Add stocks to your watchlist to enable scanning functionality
            </p>
          </div>
        ) : (
          <>
            <h3 className="text-sm font-medium mb-2">Preset Scans</h3>
            <div className="space-y-2">
              <ScanCard 
                title="Unusual Volume" 
                description="Stocks with 2x+ average volume"
                onClick={() => runScan("unusual-volume")}
                disabled={watchlist.length === 0 || isLoading}
              />
              <ScanCard 
                title="Insider Buying" 
                description="Recent insider purchases"
                onClick={() => runScan("insider-buying")}
                disabled={watchlist.length === 0 || isLoading}
              />
              <ScanCard 
                title="Hedge Fund Buys" 
                description="New institutional positions"
                onClick={() => runScan("hedge-fund-buys")}
                disabled={watchlist.length === 0 || isLoading}
              />
              <ScanCard 
                title="RSI Oversold" 
                description="RSI below 30 on daily timeframe"
                onClick={() => runScan("rsi-oversold")}
                disabled={watchlist.length === 0 || isLoading}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
} 