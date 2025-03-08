"use client"

import React, { useState } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

// Dynamically import ApexCharts to avoid SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false })

interface MarketHeatmapProps {
  data: {
    sectors: {
      name: string
      change: number
      marketCap: number
      stocks: {
        symbol: string
        name: string
        change: number
        marketCap: number
      }[]
    }[]
  }
}

export function MarketHeatmap({ data }: MarketHeatmapProps) {
  const [timeframe, setTimeframe] = useState<"1D" | "1W" | "1M" | "3M" | "1Y">("1D")
  const [view, setView] = useState<"sector" | "stocks">("sector")
  
  // Format data for the treemap
  const formatData = () => {
    if (view === "sector") {
      return data.sectors.map(sector => ({
        x: sector.name,
        y: sector.marketCap,
        fillColor: getColorByPercentChange(sector.change),
        change: sector.change,
      }))
    } else {
      // For stocks view, flatten all stocks
      return data.sectors.flatMap(sector => 
        sector.stocks.map(stock => ({
          x: stock.symbol,
          y: stock.marketCap,
          fillColor: getColorByPercentChange(stock.change),
          change: stock.change,
          sector: sector.name,
        }))
      )
    }
  }
  
  // Get color based on percent change
  const getColorByPercentChange = (change: number) => {
    // Red to green gradient based on change
    if (change <= -3) return "#ef4444" // deep red
    if (change <= -2) return "#f87171" // red
    if (change <= -1) return "#fca5a5" // light red
    if (change <= -0.5) return "#fee2e2" // very light red
    if (change <= 0) return "#f3f4f6" // neutral
    if (change <= 0.5) return "#dcfce7" // very light green
    if (change <= 1) return "#86efac" // light green
    if (change <= 2) return "#4ade80" // green
    return "#22c55e" // deep green
  }

  const series = [
    {
      data: formatData(),
    },
  ]

  const options = {
    chart: {
      type: "treemap",
      toolbar: {
        show: false,
      },
    },
    legend: {
      show: false,
    },
    title: {
      text: view === "sector" ? "Sector Performance" : "Stock Performance",
      align: "center",
      style: {
        fontSize: "16px",
      },
    },
    dataLabels: {
      enabled: true,
      style: {
        fontSize: "12px",
      },
      formatter: function(text: string, op: { data: { change: number }}) {
        return text + ` (${op.data.change >= 0 ? '+' : ''}${op.data.change.toFixed(2)}%)`
      },
    },
    tooltip: {
      y: {
        formatter: function(value: number, { series, seriesIndex, dataPointIndex, w }: { 
          series: any[],
          seriesIndex: number,
          dataPointIndex: number,
          w: { config: { series: Array<{ data: Array<{ x: string, change: number }> }> } }
        }) {
          const data = w.config.series[seriesIndex].data[dataPointIndex]
          const formattedCap = (value / 1e9).toFixed(2) + "B"
          return `${data.x}: $${formattedCap} (${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%)`
        }
      }
    },
    plotOptions: {
      treemap: {
        distributed: true,
        enableShades: false,
      },
    },
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between px-6">
        <CardTitle>Market Heatmap</CardTitle>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setView("sector")}
              className={view === "sector" ? "bg-primary text-primary-foreground" : ""}
            >
              By Sector
            </Button>
            <Button
              variant="outline" 
              size="sm"
              onClick={() => setView("stocks")}
              className={view === "stocks" ? "bg-primary text-primary-foreground" : ""}
            >
              By Stock
            </Button>
          </div>
          <div className="flex items-center gap-1">
            {["1D", "1W", "1M", "3M", "1Y"].map((period) => (
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
        <div className="flex items-center justify-center gap-2 mb-4">
          <Badge variant="outline" className="bg-[#ef4444] text-white">-3%+</Badge>
          <Badge variant="outline" className="bg-[#fca5a5] text-white">-1%+</Badge>
          <Badge variant="outline" className="bg-[#f3f4f6]">0%</Badge>
          <Badge variant="outline" className="bg-[#86efac] text-white">+1%+</Badge>
          <Badge variant="outline" className="bg-[#22c55e] text-white">+3%+</Badge>
        </div>
        {typeof window !== "undefined" ? (
          <Chart
            options={options}
            series={series}
            type="treemap"
            height={500}
          />
        ) : (
          <div className="flex items-center justify-center h-[500px]">
            <span className="text-muted-foreground">Loading heatmap...</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 