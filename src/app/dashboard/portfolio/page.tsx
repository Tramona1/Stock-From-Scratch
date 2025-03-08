"use client"

import { useState } from "react"
import { Container } from "@/components/ui/Container"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowUp, ArrowDown, Plus, Filter, RefreshCw, Download } from "lucide-react"
import { PortfolioPerformanceChart } from "@/components/dashboard/charts/PortfolioPerformanceChart"

// Mock portfolio data
const mockPortfolioData = {
  dates: Array.from({ length: 90 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (90 - i))
    return date.toISOString().split('T')[0]
  }),
  values: Array.from({ length: 90 }, (_, i) => {
    // Generate a semi-realistic portfolio value movement
    const trend = 100000 + (i * 300) + Math.sin(i / 10) * 5000
    const noise = (Math.random() - 0.5) * 2000
    return trend + noise
  }),
  initialValue: 100000,
  currentValue: 127350,
}

// Mock benchmark data (e.g., S&P 500)
const mockBenchmarkData = {
  name: "S&P 500",
  values: Array.from({ length: 90 }, (_, i) => {
    // Generate a semi-realistic benchmark movement
    const trend = 4500 + (i * 10) + Math.sin(i / 8) * 200
    const noise = (Math.random() - 0.5) * 100
    return trend + noise
  }),
}

// Mock positions data
const mockPositions = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    quantity: 50,
    avgPrice: 150.75,
    currentPrice: 182.63,
    value: 9131.50,
    gain: 1593.50,
    gainPercent: 21.14,
    allocation: 7.17,
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    quantity: 25,
    avgPrice: 290.45,
    currentPrice: 337.18,
    value: 8429.50,
    gain: 1168.25,
    gainPercent: 16.09,
    allocation: 6.62,
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    quantity: 30,
    avgPrice: 200.50,
    currentPrice: 791.12,
    value: 23733.60,
    gain: 17718.60,
    gainPercent: 294.53,
    allocation: 18.64,
  },
  {
    symbol: "AMZN",
    name: "Amazon.com Inc.",
    quantity: 40,
    avgPrice: 110.25,
    currentPrice: 178.75,
    value: 7150.00,
    gain: 2740.00,
    gainPercent: 62.13,
    allocation: 5.61,
  },
  {
    symbol: "GOOG",
    name: "Alphabet Inc.",
    quantity: 20,
    avgPrice: 120.30,
    currentPrice: 164.32,
    value: 3286.40,
    gain: 880.40,
    gainPercent: 36.59,
    allocation: 2.58,
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    quantity: 35,
    avgPrice: 220.75,
    currentPrice: 177.29,
    value: 6205.15,
    gain: -1520.60,
    gainPercent: -19.69,
    allocation: 4.87,
  },
  {
    symbol: "CASH",
    name: "Cash & Equivalents",
    quantity: 1,
    avgPrice: 69414.00,
    currentPrice: 69414.00,
    value: 69414.00,
    gain: 0,
    gainPercent: 0,
    allocation: 54.51,
  },
]

export default function PortfolioPage() {
  return (
    <div className="py-6">
      <Container>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Position
            </Button>
          </div>
        </div>
        
        <div className="grid gap-6">
          <PortfolioPerformanceChart 
            portfolioData={mockPortfolioData}
            benchmarkData={mockBenchmarkData}
          />
          
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Positions</CardTitle>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  Filter
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Avg. Price</TableHead>
                    <TableHead className="text-right">Current Price</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                    <TableHead className="text-right">Gain/Loss</TableHead>
                    <TableHead className="text-right">Allocation</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockPositions.map((position) => (
                    <TableRow key={position.symbol}>
                      <TableCell className="font-medium">{position.symbol}</TableCell>
                      <TableCell>{position.name}</TableCell>
                      <TableCell className="text-right">{position.quantity.toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        ${position.avgPrice.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        ${position.currentPrice.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        ${position.value.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          {position.gain !== 0 && (
                            position.gain > 0 
                              ? <ArrowUp className="h-3 w-3 text-green-500" /> 
                              : <ArrowDown className="h-3 w-3 text-red-500" />
                          )}
                          <span className={position.gain > 0 ? "text-green-500" : position.gain < 0 ? "text-red-500" : ""}>
                            ${Math.abs(position.gain).toFixed(2)}
                            <span className="text-xs ml-1">
                              ({position.gain > 0 ? "+" : ""}{position.gainPercent.toFixed(2)}%)
                            </span>
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {position.allocation.toFixed(2)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </Container>
    </div>
  )
} 