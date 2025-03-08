"use client"

import * as React from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

const SAMPLE_TICKERS = [
  { symbol: "AAPL", name: "Apple Inc." },
  { symbol: "MSFT", name: "Microsoft Corporation" },
  { symbol: "GOOGL", name: "Alphabet Inc." },
  { symbol: "TSLA", name: "Tesla Inc." },
  { symbol: "NVDA", name: "NVIDIA Corporation" },
]

interface TickerInputProps {
  onAdd?: (ticker: string) => void
}

export function TickerInput({ onAdd }: TickerInputProps) {
  const [search, setSearch] = React.useState("")
  const [selectedTickers, setSelectedTickers] = React.useState<string[]>([])

  const handleSuggestionClick = (symbol: string) => {
    if (!selectedTickers.includes(symbol)) {
      setSelectedTickers([...selectedTickers, symbol])
      onAdd?.(symbol)
    }
    setSearch("")
  }

  const handleRemoveTicker = (symbol: string) => {
    setSelectedTickers(selectedTickers.filter((t) => t !== symbol))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (search && !selectedTickers.includes(search.toUpperCase())) {
      const ticker = search.toUpperCase()
      setSelectedTickers([...selectedTickers, ticker])
      onAdd?.(ticker)
      setSearch("")
    }
  }

  return (
    <div className="w-full max-w-sm">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Add ticker (e.g., AAPL)"
          className="flex-1"
        />
        <Button type="submit" size="sm">
          Add
        </Button>
      </form>

      <div className="mt-2">
        <div className="flex flex-wrap gap-2">
          {selectedTickers.map((ticker) => (
            <Badge key={ticker} variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">
              {ticker}
              <button onClick={() => handleRemoveTicker(ticker)} className="ml-1 hover:text-primary-foreground">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      </div>

      {search && (
        <div className="mt-2 rounded-lg border bg-card p-2">
          <div className="text-xs font-medium text-muted-foreground mb-2">Suggestions:</div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_TICKERS.filter((t) => t.symbol.toLowerCase().includes(search.toLowerCase())).map((ticker) => (
              <Badge
                key={ticker.symbol}
                variant="outline"
                className="cursor-pointer hover:bg-primary/10"
                onClick={() => handleSuggestionClick(ticker.symbol)}
              >
                {ticker.symbol}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 