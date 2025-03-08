"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowDown, ArrowUp, Plus, RefreshCw, X, Loader2, AlertTriangle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useUser } from "@clerk/nextjs"
import { useWatchlist } from "@/context/WatchlistContext"

export function Watchlist() {
  const { isLoaded, isSignedIn } = useUser()
  const { 
    watchlist, 
    isLoading, 
    isAdding, 
    error, 
    addToWatchlist, 
    removeFromWatchlist,
    refreshWatchlist
  } = useWatchlist()
  const [newTickerInput, setNewTickerInput] = useState("")

  // Handle form submission
  const handleAddTicker = (e: React.FormEvent) => {
    e.preventDefault()
    addToWatchlist(newTickerInput)
    setNewTickerInput("")
  }

  // If not signed in, show a message
  if (isLoaded && !isSignedIn) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
        </CardHeader>
        <CardContent className="text-center py-6">
          <AlertTriangle className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
          <p>Please sign in to view and manage your watchlist</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>Watchlist</CardTitle>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={refreshWatchlist} 
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleAddTicker} className="flex mb-4">
          <Input
            placeholder="Add ticker (e.g., AAPL)"
            value={newTickerInput}
            onChange={(e) => setNewTickerInput(e.target.value)}
            className="mr-2"
            disabled={isAdding}
          />
          <Button 
            type="submit"
            size="sm" 
            disabled={isAdding || !newTickerInput.trim()}
          >
            {isAdding ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Plus className="h-4 w-4 mr-1" />
            )}
            Add
          </Button>
        </form>
        
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error || watchlist.length === 0 ? (
          <div className="text-center py-6 flex flex-col items-center justify-center h-40">
            <AlertTriangle className="h-10 w-10 text-muted-foreground mb-2" />
            <p className="text-muted-foreground font-medium">Your watchlist is empty</p>
            <p className="text-muted-foreground text-sm mt-1">
              Add tickers using the form above
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {watchlist.map((stock) => (
              <div
                key={stock.id || stock.symbol}
                className="flex items-center justify-between p-2 bg-muted/50 rounded-md"
              >
                <div>
                  <div className="flex items-center">
                    <span className="font-bold mr-2">{stock.symbol}</span>
                    <Badge variant={stock.change > 0 ? "outline" : stock.change < 0 ? "destructive" : "secondary"} className="h-5">
                      {stock.change > 0 ? (
                        <ArrowUp className="h-3 w-3 mr-1" />
                      ) : stock.change < 0 ? (
                        <ArrowDown className="h-3 w-3 mr-1" />
                      ) : null}
                      {typeof stock.change === 'number' ? Math.abs(stock.change).toFixed(2) : '0.00'}%
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">Vol: {stock.volume}</div>
                </div>
                <div className="flex items-center">
                  <span className="text-lg font-semibold mr-3">
                    ${typeof stock.price === 'number' ? stock.price.toFixed(2) : '0.00'}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => removeFromWatchlist(stock.symbol)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
} 