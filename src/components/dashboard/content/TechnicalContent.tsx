"use client"

import React, { useState } from "react"
import { Search, Filter, Bot, ArrowUp, ArrowDown, LineChart, BarChart, Bell } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatCurrency } from "@/lib/utils"

const technicalData = [
  {
    id: 1,
    ticker: "AAPL",
    name: "Apple Inc.",
    signal: "Bullish",
    pattern: "Golden Cross",
    timeframe: "Daily",
    price: 175.32,
    change: 2.34,
    volume: 67829143,
    date: "2023-06-10",
    description: "50-day moving average crosses above the 200-day moving average, indicating potential upward momentum."
  },
  {
    id: 2,
    ticker: "MSFT",
    name: "Microsoft Corp.",
    signal: "Bullish",
    pattern: "Cup and Handle",
    timeframe: "Daily",
    price: 315.75,
    change: 1.45,
    volume: 23456789,
    date: "2023-06-09",
    description: "Price forms a cup shape followed by a handle, suggesting potential breakout to the upside."
  },
  // Add more mock data
]

export function TechnicalContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredData, setFilteredData] = useState(technicalData)
  
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    
    const filtered = technicalData.filter(
      (item) =>
        item.ticker.toLowerCase().includes(query.toLowerCase()) ||
        item.name.toLowerCase().includes(query.toLowerCase()) ||
        item.pattern.toLowerCase().includes(query.toLowerCase()) ||
        item.signal.toLowerCase().includes(query.toLowerCase())
    )
    
    setFilteredData(filtered)
  }
  
  function TechnicalCard({ signal }: { signal: typeof technicalData[0] }) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold">{signal.ticker}</h3>
                <p className="text-sm text-muted-foreground">{signal.name}</p>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={signal.signal === "Bullish" ? "success" : "destructive"}>
                  {signal.signal}
                </Badge>
                <span className="text-sm">{signal.timeframe}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="font-medium">{formatCurrency(signal.price)}</div>
              <div className={signal.change > 0 ? "text-green-500 flex items-center justify-end" : "text-red-500 flex items-center justify-end"}>
                {signal.change > 0 ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
                {Math.abs(signal.change)}%
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-medium">Pattern:</span>
              <span>{signal.pattern}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Volume:</span>
              <span>{signal.volume.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Date:</span>
              <span>{signal.date}</span>
            </div>
            <p className="text-sm text-muted-foreground mt-2">{signal.description}</p>
            <div className="flex justify-between mt-4">
              <Button variant="outline" size="sm" className="gap-1">
                <LineChart className="h-4 w-4" />
                View Chart
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <Bell className="h-4 w-4" />
                Set Alert
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-2 items-center">
          <Input 
            placeholder="Search signals or tickers..." 
            className="max-w-sm" 
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
          />
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
        <Button variant="outline" className="gap-2">
          <Bot className="h-4 w-4" />
          Ask AI About Patterns
        </Button>
      </div>
      
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Signals</TabsTrigger>
          <TabsTrigger value="bullish">Bullish</TabsTrigger>
          <TabsTrigger value="bearish">Bearish</TabsTrigger>
          <TabsTrigger value="reversal">Reversal</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4 mt-4">
          {filteredData.map((signal) => (
            <TechnicalCard key={signal.id} signal={signal} />
          ))}
        </TabsContent>
        <TabsContent value="bullish" className="space-y-4 mt-4">
          {filteredData
            .filter((signal) => signal.signal === "Bullish")
            .map((signal) => (
              <TechnicalCard key={signal.id} signal={signal} />
            ))}
        </TabsContent>
        <TabsContent value="bearish" className="space-y-4 mt-4">
          {filteredData
            .filter((signal) => signal.signal === "Bearish")
            .map((signal) => (
              <TechnicalCard key={signal.id} signal={signal} />
            ))}
        </TabsContent>
        <TabsContent value="reversal" className="space-y-4 mt-4">
          {filteredData
            .filter((signal) => signal.pattern.includes("Reversal"))
            .map((signal) => (
              <TechnicalCard key={signal.id} signal={signal} />
            ))}
        </TabsContent>
      </Tabs>
    </div>
  )
} 