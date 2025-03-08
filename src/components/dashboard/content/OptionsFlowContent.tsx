"use client"

import React, { useState } from "react"
import { Search, Filter, ArrowUp, ArrowDown, Zap, AlertTriangle, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatCurrency, formatNumber } from "@/lib/utils"

const flowData = [
  {
    id: 1,
    ticker: "AAPL",
    name: "Apple Inc.",
    type: "Call",
    strike: 190,
    expiration: "Jun 21, 2024",
    premium: 1254000,
    contracts: 1500,
    sentiment: "Bullish",
    price: 175.32,
    change: 2.34,
    time: "10:32 AM",
    oi: 15420,
    iv: 0.32,
  },
  {
    id: 2,
    ticker: "NVDA",
    name: "NVIDIA Corporation",
    type: "Put",
    strike: 850,
    expiration: "Aug 16, 2024",
    premium: 2130000,
    contracts: 430,
    sentiment: "Bearish",
    price: 870.35,
    change: -3.21,
    time: "11:45 AM",
    oi: 8750,
    iv: 0.55,
  },
  // More data can be added here
]

export function OptionsFlowContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredData, setFilteredData] = useState(flowData)
  
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    
    const filtered = flowData.filter(
      (item) =>
        item.ticker.toLowerCase().includes(query.toLowerCase()) ||
        item.name.toLowerCase().includes(query.toLowerCase()) ||
        item.type.toLowerCase().includes(query.toLowerCase()) ||
        item.sentiment.toLowerCase().includes(query.toLowerCase())
    )
    
    setFilteredData(filtered)
  }

  function FlowCard({ flow }: { flow: typeof flowData[0] }) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold">{flow.ticker}</h3>
                <p className="text-sm text-muted-foreground">{flow.name}</p>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={flow.type === "Call" ? "success" : "destructive"}>
                  {flow.type}
                </Badge>
                <Badge variant="outline">
                  ${flow.strike}
                </Badge>
                <span className="text-sm">{flow.expiration}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="font-medium">{formatCurrency(flow.price)}</div>
              <div className={flow.change > 0 ? "text-green-500 flex items-center justify-end" : "text-red-500 flex items-center justify-end"}>
                {flow.change > 0 ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
                {Math.abs(flow.change)}%
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-medium">Premium:</span>
              <span className="font-semibold">{formatCurrency(flow.premium)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Contracts:</span>
              <span>{flow.contracts.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Time:</span>
              <span>{flow.time}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="flex flex-col text-center p-2 bg-muted/30 rounded-md">
                <span className="text-xs text-muted-foreground">Open Interest</span>
                <span className="font-medium">{formatNumber(flow.oi)}</span>
              </div>
              <div className="flex flex-col text-center p-2 bg-muted/30 rounded-md">
                <span className="text-xs text-muted-foreground">Implied Vol</span>
                <span className="font-medium">{(flow.iv * 100).toFixed(1)}%</span>
              </div>
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
            placeholder="Search options flow..." 
            className="max-w-sm" 
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
          />
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
        <Button variant="outline" className="gap-2">
          <Zap className="h-4 w-4" />
          Live Flow
        </Button>
      </div>
      
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="bullish">Bullish</TabsTrigger>
          <TabsTrigger value="bearish">Bearish</TabsTrigger>
          <TabsTrigger value="calls">Calls</TabsTrigger>
          <TabsTrigger value="puts">Puts</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4 mt-4">
          {filteredData.map((flow) => (
            <FlowCard key={flow.id} flow={flow} />
          ))}
        </TabsContent>
        <TabsContent value="bullish" className="space-y-4 mt-4">
          {filteredData
            .filter((flow) => flow.sentiment === "Bullish")
            .map((flow) => (
              <FlowCard key={flow.id} flow={flow} />
            ))}
        </TabsContent>
        <TabsContent value="bearish" className="space-y-4 mt-4">
          {filteredData
            .filter((flow) => flow.sentiment === "Bearish")
            .map((flow) => (
              <FlowCard key={flow.id} flow={flow} />
            ))}
        </TabsContent>
        <TabsContent value="calls" className="space-y-4 mt-4">
          {filteredData
            .filter((flow) => flow.type === "Call")
            .map((flow) => (
              <FlowCard key={flow.id} flow={flow} />
            ))}
        </TabsContent>
        <TabsContent value="puts" className="space-y-4 mt-4">
          {filteredData
            .filter((flow) => flow.type === "Put")
            .map((flow) => (
              <FlowCard key={flow.id} flow={flow} />
            ))}
        </TabsContent>
      </Tabs>
    </div>
  )
} 