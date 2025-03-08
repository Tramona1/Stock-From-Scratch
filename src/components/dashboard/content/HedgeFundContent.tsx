"use client"

import { useState } from "react"
import { Search, ArrowUpRight, ArrowDownRight, Bot, Filter } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const hedgeFundData = [
  {
    id: 1,
    fund: "Renaissance Technologies",
    ticker: "NVDA",
    action: "Increased",
    filingDate: "2023-05-15",
    shares: 1200000,
    value: 580000000,
    changePercent: 25,
  },
  {
    id: 2,
    fund: "Citadel Advisors",
    ticker: "AAPL",
    action: "New Position",
    filingDate: "2023-05-12",
    shares: 2500000,
    value: 450000000,
    changePercent: 100,
  },
  {
    id: 3,
    fund: "Bridgewater Associates",
    ticker: "TSLA",
    action: "Decreased",
    filingDate: "2023-05-10",
    shares: 500000,
    value: 120000000,
    changePercent: -15,
  },
  {
    id: 4,
    fund: "Point72 Asset Management",
    ticker: "MSFT",
    action: "Increased",
    filingDate: "2023-05-08",
    shares: 800000,
    value: 320000000,
    changePercent: 10,
  },
  {
    id: 5,
    fund: "Two Sigma Investments",
    ticker: "AMZN",
    action: "New Position",
    filingDate: "2023-05-05",
    shares: 300000,
    value: 110000000,
    changePercent: 100,
  },
  {
    id: 6,
    fund: "D.E. Shaw & Co",
    ticker: "META",
    action: "Decreased",
    filingDate: "2023-05-02",
    shares: 400000,
    value: 130000000,
    changePercent: -20,
  },
]

export function HedgeFundContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredData, setFilteredData] = useState(hedgeFundData)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (!query) {
      setFilteredData(hedgeFundData)
      return
    }
    
    const lowercaseQuery = query.toLowerCase()
    const filtered = hedgeFundData.filter(
      (item) =>
        item.fund.toLowerCase().includes(lowercaseQuery) ||
        item.ticker.toLowerCase().includes(lowercaseQuery)
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
            placeholder="Search fund or ticker..." 
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
          Ask AI About Hedge Funds
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent 13F Filings</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fund</TableHead>
                <TableHead>Ticker</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Filing Date</TableHead>
                <TableHead>Shares</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.fund}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-primary/10 text-primary">
                      ${item.ticker}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        item.action === "Increased" || item.action === "New Position"
                          ? "secondary"
                          : "outline"
                      }
                    >
                      {item.action}
                    </Badge>
                  </TableCell>
                  <TableCell>{item.filingDate}</TableCell>
                  <TableCell>{item.shares.toLocaleString()}</TableCell>
                  <TableCell>{formatLargeNumber(item.value)}</TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      {item.changePercent > 0 ? (
                        <ArrowUpRight className="mr-1 h-4 w-4 text-green-500" />
                      ) : (
                        <ArrowDownRight className="mr-1 h-4 w-4 text-red-500" />
                      )}
                      <span
                        className={
                          item.changePercent > 0 ? "text-green-500" : "text-red-500"
                        }
                      >
                        {Math.abs(item.changePercent)}%
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
} 