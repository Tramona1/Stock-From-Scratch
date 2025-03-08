"use client"

import { useState } from "react"
import { Search, ArrowUpRight, ArrowDownRight, Bot, Filter, ExternalLink } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const insiderData = [
  {
    id: 1,
    name: "Tim Cook",
    position: "CEO",
    ticker: "AAPL",
    transactionType: "Sell",
    date: "2023-05-15",
    shares: 100000,
    avgPrice: 180.25,
    value: 18025000,
    ownership: 850000,
  },
  {
    id: 2,
    name: "Lisa Su",
    position: "CEO",
    ticker: "AMD",
    transactionType: "Buy",
    date: "2023-05-10",
    shares: 25000,
    avgPrice: 92.35,
    value: 2308750,
    ownership: 225000,
  },
  {
    id: 3,
    name: "Satya Nadella",
    position: "CEO",
    ticker: "MSFT",
    transactionType: "Sell",
    date: "2023-05-08",
    shares: 50000,
    avgPrice: 335.75,
    value: 16787500,
    ownership: 650000,
  },
  {
    id: 4,
    name: "Jensen Huang",
    position: "CEO",
    ticker: "NVDA",
    transactionType: "Sell",
    date: "2023-05-05",
    shares: 30000,
    avgPrice: 475.50,
    value: 14265000,
    ownership: 1200000,
  },
  {
    id: 5,
    name: "Mark Zuckerberg",
    position: "CEO",
    ticker: "META",
    transactionType: "Sell",
    date: "2023-05-02",
    shares: 40000,
    avgPrice: 312.80,
    value: 12512000,
    ownership: 350000000,
  },
]

export function InsiderTradingContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredData, setFilteredData] = useState(insiderData)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (!query) {
      setFilteredData(insiderData)
      return
    }
    
    const lowercaseQuery = query.toLowerCase()
    const filtered = insiderData.filter(
      (item) =>
        item.name.toLowerCase().includes(lowercaseQuery) ||
        item.ticker.toLowerCase().includes(lowercaseQuery) ||
        item.position.toLowerCase().includes(lowercaseQuery)
    )
    setFilteredData(filtered)
  }

  // Helper function to format large numbers
  const formatLargeNumber = (num: number) => {
    if (num >= 1000000000) {
      return `$${(num / 1000000000).toFixed(2)}B`
    }
    if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(2)}M`
    }
    if (num >= 1000) {
      return `$${(num / 1000).toFixed(2)}K`
    }
    return `$${num}`
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-2 items-center">
          <Input 
            placeholder="Search insider, position, or ticker..." 
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
          Ask AI About Insider Trades
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Form 4 Filings</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Position</TableHead>
                <TableHead>Ticker</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Shares</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Ownership</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell>{item.position}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-primary/10 text-primary">
                      ${item.ticker}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        item.transactionType === "Buy"
                          ? "secondary"
                          : "outline"
                      }
                    >
                      {item.transactionType}
                    </Badge>
                  </TableCell>
                  <TableCell>{item.date}</TableCell>
                  <TableCell>{item.shares.toLocaleString()}</TableCell>
                  <TableCell>${item.avgPrice.toFixed(2)}</TableCell>
                  <TableCell>{formatLargeNumber(item.value)}</TableCell>
                  <TableCell>{item.ownership.toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
} 