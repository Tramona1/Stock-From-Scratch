"use client"

import { useState } from "react"
import { Bot } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"

interface Alert {
  id: number
  title: string
  description?: string
  time?: string
  isNew?: boolean
  type: string
  ticker: string
  details: string
  timestamp: string
  severity: string
}

const alertItems = [
  {
    id: 1,
    type: "hedge-fund",
    ticker: "NVDA",
    title: "Renaissance Technologies Increases Position",
    details: "Added 1.2M shares worth approximately $580M",
    timestamp: "2 hours ago",
    severity: "high",
  },
  {
    id: 2, 
    type: "insider",
    ticker: "AAPL",
    title: "Tim Cook (CEO) Sold Shares",
    details: "100,000 shares worth $18M following vesting schedule",
    timestamp: "4 hours ago",
    severity: "medium",
  },
  {
    id: 3,
    type: "options",
    ticker: "TSLA",
    title: "Large Put Purchase",
    details: "$5M in June 2024 puts purchased at $200 strike",
    timestamp: "1 hour ago",
    severity: "high",
  },
  {
    id: 4,
    type: "technical",
    ticker: "AAPL",
    title: "Golden Cross Detected",
    details: "50-day MA crosses above 200-day MA",
    timestamp: "Today",
    severity: "medium",
  },
  {
    id: 5,
    type: "market",
    ticker: "SPY",
    title: "Unusual Volume",
    details: "Trading at 2.5x average daily volume",
    timestamp: "30 minutes ago",
    severity: "medium",
  },
]

export function AlertsContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredAlerts, setFilteredAlerts] = useState(alertItems)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (!query) {
      setFilteredAlerts(alertItems)
      return
    }
    
    const lowercaseQuery = query.toLowerCase()
    const filtered = alertItems.filter(
      (alert) =>
        alert.ticker.toLowerCase().includes(lowercaseQuery) ||
        alert.title.toLowerCase().includes(lowercaseQuery) ||
        alert.details.toLowerCase().includes(lowercaseQuery)
    )
    setFilteredAlerts(filtered)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Input 
          placeholder="Search alerts..." 
          className="max-w-sm" 
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
        />
        <Button variant="outline" className="gap-2">
          <Bot className="h-4 w-4" />
          Ask AI About Alerts
        </Button>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Alerts</TabsTrigger>
          <TabsTrigger value="hedge-fund">Hedge Fund</TabsTrigger>
          <TabsTrigger value="insider">Insider</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4 mt-4">
          {filteredAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </TabsContent>
        <TabsContent value="hedge-fund" className="space-y-4 mt-4">
          {filteredAlerts
            .filter((alert) => alert.type === "hedge-fund")
            .map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
        </TabsContent>
        <TabsContent value="insider" className="space-y-4 mt-4">
          {filteredAlerts
            .filter((alert) => alert.type === "insider")
            .map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
        </TabsContent>
        <TabsContent value="options" className="space-y-4 mt-4">
          {filteredAlerts
            .filter((alert) => alert.type === "options")
            .map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
        </TabsContent>
        <TabsContent value="technical" className="space-y-4 mt-4">
          {filteredAlerts
            .filter((alert) => alert.type === "technical")
            .map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AlertCard({ alert }: { alert: Alert }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-primary/10 text-primary">
                ${alert.ticker}
              </Badge>
              <Badge
                variant={
                  alert.severity === "high"
                    ? "destructive"
                    : alert.severity === "medium"
                    ? "secondary"
                    : "outline"
                }
              >
                {alert.type === "hedge-fund" && "Hedge Fund Activity"}
                {alert.type === "insider" && "Insider Trading"}
                {alert.type === "options" && "Options Flow"}
                {alert.type === "technical" && "Technical Signal"}
                {alert.type === "market" && "Market Activity"}
              </Badge>
              <span className="text-xs text-muted-foreground">{alert.timestamp}</span>
            </div>
            <h3 className="font-semibold">{alert.title}</h3>
            <p className="text-sm text-muted-foreground">{alert.details}</p>
          </div>
          <Button variant="ghost" size="sm">
            <Bot className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 