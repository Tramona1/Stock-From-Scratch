"use client"

import React, { useState } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LineChart, Loader2 } from "lucide-react"

// Dynamically import ApexCharts to avoid SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false })

interface StockChartProps {
  symbol: string
  data: {
    dates: string[]
    prices: number[]
    volumes: number[]
  }
  companyName?: string
  currentPrice?: number
  priceChange?: number
  percentChange?: number
}

export function StockChart({
  symbol,
  data,
  companyName = "",
  currentPrice,
  priceChange,
  percentChange,
}: StockChartProps) {
  const [chartType, setChartType] = useState<"line" | "candlestick" | "area">("area")
  const [timeframe, setTimeframe] = useState<"1D" | "1W" | "1M" | "3M" | "1Y" | "5Y">("1M")
  
  // Format the data for ApexCharts
  const series = [
    {
      name: symbol,
      data: data.prices,
    },
  ]

  const options = {
    chart: {
      type: chartType,
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
      categories: data.dates,
      labels: {
        rotate: -45,
        style: {
          fontSize: '10px',
        },
      },
    },
    tooltip: {
      x: {
        format: "dd MMM yyyy",
      },
    },
    yaxis: {
      labels: {
        formatter: function (value: number) {
          return "$" + value.toFixed(2)
        },
      },
    },
    colors: ["#3B82F6"],
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.2,
        stops: [0, 90, 100],
      },
    },
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between px-6">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle>{symbol}</CardTitle>
            {companyName && <span className="text-sm text-muted-foreground">{companyName}</span>}
          </div>
          {currentPrice && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold">${currentPrice.toFixed(2)}</span>
              {percentChange && (
                <Badge variant={percentChange >= 0 ? "secondary" : "destructive"}>
                  {percentChange >= 0 ? "+" : ""}{percentChange.toFixed(2)}%
                </Badge>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1">
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("area")}
              className={chartType === "area" ? "bg-primary text-primary-foreground" : ""}
            >
              Area
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("line")}
              className={chartType === "line" ? "bg-primary text-primary-foreground" : ""}
            >
              Line
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("candlestick")}
              className={chartType === "candlestick" ? "bg-primary text-primary-foreground" : ""}
            >
              Candlestick
            </Button>
          </div>
          <div className="flex items-center gap-1">
            {["1D", "1W", "1M", "3M", "1Y", "5Y"].map((period) => (
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
      <CardContent className="p-0">
        {typeof window !== "undefined" ? (
          <Chart
            options={options}
            series={series}
            type={chartType}
            height={400}
          />
        ) : (
          <div className="flex items-center justify-center h-[400px]">
            <LineChart className="h-8 w-8 animate-pulse text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading chart...</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 