"use client"

import { useState } from "react"
import { Container } from "@/components/ui/Container"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, BarChart3 } from "lucide-react"
import { StockChart } from "@/components/dashboard/charts/StockChart"
import { ComparisonChart } from "@/components/dashboard/charts/ComparisonChart"
import { MarketHeatmap } from "@/components/dashboard/charts/MarketHeatmap"

// Mock data for demonstration
const mockPriceData = {
  dates: Array.from({ length: 90 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (90 - i))
    return date.toISOString().split('T')[0]
  }),
  prices: Array.from({ length: 90 }, (_, i) => {
    // Generate a semi-realistic price movement
    const trend = Math.sin(i / 10) * 20 + 150 + i / 3
    const noise = (Math.random() - 0.5) * 10
    return Math.max(50, trend + noise)
  }),
  volumes: Array.from({ length: 90 }, () => Math.floor(Math.random() * 10000000) + 1000000),
}

const mockComparisonData = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    data: {
      dates: mockPriceData.dates,
      prices: mockPriceData.prices.map(p => p * 0.9 + Math.random() * 20),
    },
    color: "#3B82F6",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    data: {
      dates: mockPriceData.dates,
      prices: mockPriceData.prices.map(p => p * 1.1 + Math.random() * 20),
    },
    color: "#10B981",
  },
  {
    symbol: "GOOG",
    name: "Alphabet Inc.",
    data: {
      dates: mockPriceData.dates,
      prices: mockPriceData.prices.map(p => p * 0.95 + Math.random() * 20),
    },
    color: "#F59E0B",
  },
  {
    symbol: "AMZN",
    name: "Amazon.com Inc.",
    data: {
      dates: mockPriceData.dates,
      prices: mockPriceData.prices.map(p => p * 1.05 + Math.random() * 20),
    },
    color: "#EC4899",
  },
]

const mockHeatmapData = {
  sectors: [
    {
      name: "Technology",
      change: 2.3,
      marketCap: 10500000000000,
      stocks: [
        { symbol: "AAPL", name: "Apple Inc.", change: 1.5, marketCap: 2500000000000 },
        { symbol: "MSFT", name: "Microsoft Corp.", change: 3.2, marketCap: 2400000000000 },
        { symbol: "NVDA", name: "NVIDIA Corp.", change: 4.1, marketCap: 1100000000000 },
        { symbol: "GOOG", name: "Alphabet Inc.", change: 1.8, marketCap: 1800000000000 },
      ],
    },
    {
      name: "Consumer Cyclical",
      change: -1.2,
      marketCap: 5200000000000,
      stocks: [
        { symbol: "AMZN", name: "Amazon.com Inc.", change: -0.8, marketCap: 1600000000000 },
        { symbol: "TSLA", name: "Tesla Inc.", change: -2.5, marketCap: 750000000000 },
        { symbol: "HD", name: "Home Depot Inc.", change: -1.3, marketCap: 350000000000 },
        { symbol: "NKE", name: "Nike Inc.", change: -0.9, marketCap: 180000000000 },
      ],
    },
    {
      name: "Financial",
      change: 0.8,
      marketCap: 4800000000000,
      stocks: [
        { symbol: "JPM", name: "JPMorgan Chase", change: 1.2, marketCap: 480000000000 },
        { symbol: "BAC", name: "Bank of America", change: 0.7, marketCap: 320000000000 },
        { symbol: "WFC", name: "Wells Fargo", change: 0.5, marketCap: 190000000000 },
        { symbol: "GS", name: "Goldman Sachs", change: 1.1, marketCap: 130000000000 },
      ],
    },
    {
      name: "Healthcare",
      change: -0.5,
      marketCap: 4200000000000,
      stocks: [
        { symbol: "JNJ", name: "Johnson & Johnson", change: -0.3, marketCap: 420000000000 },
        { symbol: "UNH", name: "UnitedHealth Group", change: -0.7, marketCap: 450000000000 },
        { symbol: "PFE", name: "Pfizer Inc.", change: -1.1, marketCap: 180000000000 },
        { symbol: "ABBV", name: "AbbVie Inc.", change: 0.2, marketCap: 250000000000 },
      ],
    },
    {
      name: "Energy",
      change: 1.5,
      marketCap: 2800000000000,
      stocks: [
        { symbol: "XOM", name: "Exxon Mobil", change: 1.8, marketCap: 450000000000 },
        { symbol: "CVX", name: "Chevron Corp.", change: 1.3, marketCap: 320000000000 },
        { symbol: "COP", name: "ConocoPhillips", change: 1.9, marketCap: 140000000000 },
        { symbol: "SLB", name: "Schlumberger", change: 0.8, marketCap: 80000000000 },
      ],
    },
  ]
}

export default function AnalysisPage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="py-6">
      <Container>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Market Analysis</h1>
          <div className="flex items-center gap-2">
            <Input 
              placeholder="Search ticker..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-60"
            />
            <Button>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
          </div>
        </div>
        
        <Tabs defaultValue="charts">
          <TabsList className="mb-4">
            <TabsTrigger value="charts">Charts</TabsTrigger>
            <TabsTrigger value="comparison">Comparison</TabsTrigger>
            <TabsTrigger value="heatmap">Market Heatmap</TabsTrigger>
          </TabsList>
          
          <TabsContent value="charts">
            <div className="grid gap-6">
              <StockChart 
                symbol="AAPL" 
                data={mockPriceData} 
                companyName="Apple Inc."
                currentPrice={182.63}
                priceChange={2.53}
                percentChange={1.41}
              />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Key Statistics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Market Cap</p>
                        <p className="font-medium">$2.85T</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">P/E Ratio</p>
                        <p className="font-medium">30.42</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Dividend Yield</p>
                        <p className="font-medium">0.51%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">52 Week High</p>
                        <p className="font-medium">$196.74</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">52 Week Low</p>
                        <p className="font-medium">$124.17</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Avg. Volume</p>
                        <p className="font-medium">58.67M</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle>Technical Indicators</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">RSI (14)</span>
                        <Badge variant={65 < 30 ? "destructive" : 65 > 70 ? "secondary" : "outline"}>
                          65
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">MACD</span>
                        <Badge variant="secondary">Bullish</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Moving Averages</span>
                        <Badge variant="secondary">Buy</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Bollinger Bands</span>
                        <Badge variant="outline">Neutral</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Stochastic</span>
                        <Badge variant="secondary">Bullish</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Overall Signal</span>
                        <Badge variant="secondary">Buy</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="comparison">
            <ComparisonChart stocks={mockComparisonData} />
          </TabsContent>
          
          <TabsContent value="heatmap">
            <MarketHeatmap data={mockHeatmapData} />
          </TabsContent>
        </Tabs>
      </Container>
    </div>
  )
} 