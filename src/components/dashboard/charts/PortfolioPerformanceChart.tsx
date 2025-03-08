"use client"

import React, { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowUp, ArrowDown } from "lucide-react"

// Dynamically import ApexCharts to avoid SSR issues
const Chart = dynamic(
  () => import("react-apexcharts").then((mod) => mod.default),
  { ssr: false }
)

interface PortfolioPerformanceChartProps {
  portfolioData: {
    dates: string[]
    values: number[]
    initialValue: number
    currentValue: number
  }
  benchmarkData?: {
    name: string
    values: number[]
  }
}

export function PortfolioPerformanceChart({
  portfolioData,
  benchmarkData,
}: PortfolioPerformanceChartProps) {
  const [timeframe, setTimeframe] = useState<"1D" | "1W" | "1M" | "3M" | "1Y" | "5Y" | "YTD" | "MAX">("1M")
  const [chartType, setChartType] = useState<"value" | "change" | "percent">("percent")
  
  // Calculate metrics
  const absoluteChange = portfolioData.currentValue - portfolioData.initialValue
  const percentChange = (absoluteChange / portfolioData.initialValue) * 100
  const isPositive = absoluteChange >= 0

  // Process data based on selected view
  const processData = () => {
    if (chartType === "value") {
      return [
        {
          name: "Portfolio Value",
          data: portfolioData.values,
          color: "#3B82F6",
        },
        benchmarkData && {
          name: benchmarkData.name,
          data: benchmarkData.values,
          color: "#64748B",
        },
      ].filter(Boolean)
    } else {
      // For percent or change views, normalize the data
      const basePortfolioValue = portfolioData.values[0]
      const normalizedPortfolio = portfolioData.values.map((value, index) => {
        if (chartType === "percent") {
          return ((value / basePortfolioValue) - 1) * 100
        } else {
          return value - basePortfolioValue
        }
      })

      const series = [
        {
          name: "Portfolio",
          data: normalizedPortfolio,
          color: "#3B82F6",
        },
      ]

      if (benchmarkData) {
        const baseBenchmarkValue = benchmarkData.values[0]
        const normalizedBenchmark = benchmarkData.values.map((value) => {
          if (chartType === "percent") {
            return ((value / baseBenchmarkValue) - 1) * 100
          } else {
            return value - baseBenchmarkValue
          }
        })

        series.push({
          name: benchmarkData.name,
          data: normalizedBenchmark,
          color: "#64748B",
        })
      }

      return series
    }
  }

  const series = processData()

  const options = {
    chart: {
      type: "area",
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
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.2,
        stops: [0, 90, 100],
      },
    },
    xaxis: {
      categories: portfolioData.dates,
      labels: {
        rotate: -45,
        style: {
          fontSize: '10px',
        },
      },
    },
    yaxis: {
      labels: {
        formatter: function (value: number) {
          if (chartType === "value") {
            return "$" + value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")
          } else if (chartType === "percent") {
            return value.toFixed(2) + "%"
          } else {
            return "$" + value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")
          }
        },
      },
    },
    tooltip: {
      shared: true,
      intersect: false,
      y: {
        formatter: function (value: number) {
          return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
          <CardTitle>Portfolio Performance</CardTitle>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-2xl font-bold">
              ${portfolioData.currentValue.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
            </span>
            <div className="flex flex-col">
              <Badge 
                variant={isPositive ? "secondary" : "destructive"}
                className="flex items-center"
              >
                {isPositive ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
                {isPositive ? "+" : ""}{absoluteChange.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
              </Badge>
              <Badge 
                variant="outline" 
                className={`text-xs ${isPositive ? "text-green-500" : "text-red-500"}`}
              >
                {isPositive ? "+" : ""}{percentChange.toFixed(2)}%
              </Badge>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1">
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("percent")}
              className={chartType === "percent" ? "bg-primary text-primary-foreground" : ""}
            >
              %
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("value")}
              className={chartType === "value" ? "bg-primary text-primary-foreground" : ""}
            >
              Value
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setChartType("change")}
              className={chartType === "change" ? "bg-primary text-primary-foreground" : ""}
            >
              Change
            </Button>
          </div>
          <div className="flex items-center gap-1">
            {["1D", "1W", "1M", "3M", "1Y", "MAX"].map((period) => (
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
        {typeof window !== "undefined" && Chart ? (
          <Chart
            options={options}
            series={series}
            type="area"
            height={400}
          />
        ) : (
          <div className="flex items-center justify-center h-[400px]">
            <span className="text-muted-foreground">Loading chart...</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 