"use client"
import { motion } from "framer-motion"
import { 
  ArrowDown, 
  ArrowUp, 
  Bell, 
  Bot, 
  Search, 
  Zap, 
  X,
  AlertTriangle,
  PlusCircle
} from "lucide-react"
import { Container } from "@/components/ui/Container"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { TickerInput } from "@/components/dashboard/TickerInput"
import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { MarketIndicators } from "@/components/dashboard/MarketIndicators"
import { Watchlist } from "@/components/dashboard/Watchlist"
import { MarketScanner } from "@/components/dashboard/MarketScanner"
import { AiQueryInterface } from "@/components/dashboard/AiQueryInterface"
import { MockDataProvider } from './_components/MockDataProvider'
import { useWatchlist } from "@/context/WatchlistContext"

// Scanner presets
const scannerPresets = [
  { name: "Unusual Volume", description: "Stocks with 2x+ average volume" },
  { name: "Insider Buying", description: "Recent insider purchases" },
  { name: "Hedge Fund Buys", description: "New institutional positions" },
  { name: "RSI Oversold", description: "RSI below 30 on daily chart" },
]

// Combined feed data
const feedItems = [
  {
    id: 1,
    type: "hedge-fund",
    fund: "Renaissance Technologies",
    action: "Increases Position",
    ticker: "NVDA",
    details: "Added 1.2M shares worth approximately $580M",
    timestamp: "2 hours ago",
    relevance: "Your Holding",
    aiContext:
      "This hedge fund activity is relevant because it shows significant institutional movement that could impact the stock price. When large funds make moves of this size, it often signals a strong conviction about the company's future prospects.",
  },
  {
    id: 2,
    type: "insider",
    insider: "Tim Cook",
    role: "CEO",
    ticker: "AAPL",
    action: "Sold",
    details: "100,000 shares worth $18M following vesting schedule",
    timestamp: "4 hours ago",
    relevance: "Your Holding",
    aiContext:
      "Insider trading activity is significant because Tim Cook, as CEO, has direct knowledge of the company's operations. Their decision to sell shares could indicate their perspective on the company's future performance.",
  },
  {
    id: 3,
    type: "options",
    ticker: "TSLA",
    optionType: "PUT",
    details: "$5M in June 2024 puts purchased at $200 strike",
    premium: "$2.1M",
    timestamp: "1 hour ago",
    relevance: "On Your Watchlist",
    aiContext:
      "This options activity is notable because the size of the premium ($2.1M) suggests strong directional conviction from institutional traders. The put position could indicate expectations of downward price movement.",
  },
  {
    id: 4,
    type: "technical",
    ticker: "AAPL",
    signal: "Golden Cross",
    details: "50-day MA crosses above 200-day MA",
    timestamp: "Today",
    relevance: "Your Holding",
    aiContext:
      "This technical signal (Golden Cross) is important because it suggests a potential bullish price movement based on historical price patterns and momentum indicators.",
  },
  {
    id: 5,
    type: "hedge-fund",
    fund: "Citadel",
    action: "New Position",
    ticker: "AAPL",
    details: "Purchased 2.5M shares worth $450M",
    timestamp: "4 hours ago",
    relevance: "Your Holding",
    aiContext:
      "This is significant because Citadel is one of the largest hedge funds, and their new position in AAPL suggests they see value at current price levels. Their $450M investment could provide price support.",
  },
]

export default function DashboardPage() {
  const { watchlist, isLoading: isWatchlistLoading } = useWatchlist();
  const [aiChatOpen, setAiChatOpen] = useState(false);
  const [currentContext, setCurrentContext] = useState<string>("");
  const [aiQuery, setAiQuery] = useState("");
  const [newTickerInput, setNewTickerInput] = useState("");

  // Common empty state component
  const CardEmptyState = ({ message = "Add stocks to your watchlist to see data" }) => (
    <p className="text-sm text-muted-foreground text-center py-4">{message}</p>
  );

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      {/* Market indicators always show general market data */}
      <MarketIndicators />
      
      {/* Watchlist section */}
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1">
          <AiQueryInterface />
          <div className="mt-6">
            <Watchlist />
          </div>
        </div>
        <div className="lg:w-80 w-full">
          <MarketScanner />
        </div>
      </div>
    </div>
  )
} 