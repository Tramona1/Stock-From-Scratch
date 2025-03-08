"use client"

import React, { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"

// Dynamically import ApexCharts properly
const Chart = dynamic(
  () => import("react-apexcharts").then((mod) => mod.default),
  { ssr: false }
)

interface ComparisonChartProps {
  stocks: {
    symbol: string
    name: string
    data: {
      dates: string[]
      prices: number[]
    }
    color: string
  }[]
}

export function ComparisonChart({ stocks }: ComparisonChartProps) {
  const [timeframe, setTimeframe] = useState<"1D" | "1W" | "1M" | "3M" | "1Y" | "5Y">("3M")
  const [normalizeData, setNormalizeData] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")

  // For normalized view, we convert all prices to percentage changes from the start
  const series = stocks.map((stock) => {
    const baseValue = normalizeData ? stock.data.prices[0] : 1
    const normalizedPrices = stock.data.prices.map((price) => 
      normalizeData ? (price / baseValue) * 100 : price
    )
    
    return {
      name: stock.symbol,
      data: normalizedPrices,
      color: stock.color,
    }
  })

  const options = {
    chart: {
      type: "line",
      height: 350,
      toolbar: {
        show: true,
      },
      animations: {
        enabled: true,
      },
      background: 'transparent',
    },
    stroke: {
      curve: "smooth",
      width: 2,
    },
    xaxis: {
      categories: stocks[0]?.data.dates || [],
      labels: {
        rotate: -45,
        style: {
          fontSize: '10px',
        },
      },
    },
    tooltip: {
      shared: true,
      intersect: false,
      y: {
        formatter: function (value: number) {
          return normalizeData ? value.toFixed(2) + "%" : "$" + value.toFixed(2);
        },
      },
    },
    legend: {
      position: 'top',
    },
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between px-6">
        <div>
          <CardTitle>Performance Comparison</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            {normalizeData 
              ? "Normalized to 100 at start date" 
              : "Absolute price values"}
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Add ticker..."
              className="w-32 h-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Button variant="outline" size="sm" className="h-8 px-2">
              <Search className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setNormalizeData(true)}
              className={normalizeData ? "bg-primary text-primary-foreground" : ""}
            >
              Relative
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setNormalizeData(false)}
              className={!normalizeData ? "bg-primary text-primary-foreground" : ""}
            >
              Absolute
            </Button>
          </div>
          <div className="flex items-center gap-1">
            {["1W", "1M", "3M", "1Y", "5Y"].map((period) => (
              <Button
                key={period}
                variant="outline"
                size="sm"
                onClick={() => setTimeframe(period as any)}
                className={timeframe === period ? "bg-primary text-primary-foreground" : ""}
              >
                {period}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {stocks.map((stock) => (
            <Badge 
              key={stock.symbol} 
              variant="outline" 
              className="flex items-center gap-1"
            >
              <span 
                className="h-2 w-2 rounded-full" 
                style={{ backgroundColor: stock.color }}
              ></span>
              {stock.symbol} - {stock.name}
            </Badge>
          ))}
        </div>
        {typeof window !== "undefined" && Chart ? (
          <Chart
            options={options}
            series={series}
            type="line"
            height={350}
          />
        ) : (
          <div className="flex items-center justify-center h-[350px]">
            <span className="text-muted-foreground">Loading chart...</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 