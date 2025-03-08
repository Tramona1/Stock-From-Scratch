"use client"
import { Badge } from "@/components/ui/badge"

interface Alert {
  symbol: string
  content: string
  source: string
  type: string
}

export function AlertTicker() {
  const alerts: Alert[] = [
    {
      symbol: "NVDA",
      content: "Renaissance Technologies increases position by 215%",
      source: "SEC Filing 13F",
      type: "Hedge Fund Activity",
    },
    {
      symbol: "JPM",
      content: "Jamie Dimon sells 33% of holdings ($58M)",
      source: "SEC Form 4",
      type: "Insider Trading",
    },
    {
      symbol: "TSLA",
      content: "Blackrock decreases position by 8.3%",
      source: "13F Filing",
      type: "Institutional Activity",
    },
  ]

  return (
    <div className="bg-gradient-to-r from-white to-blue-50 py-3 overflow-hidden border-b border-blue-100">
      <div className="flex items-center animate-[marquee_40s_linear_infinite] whitespace-nowrap">
        {alerts.concat(alerts).map((alert, i) => (
          <div key={i} className="flex items-center mx-8">
            <Badge variant="secondary" className="bg-blue-100 text-blue-700 mr-2">
              {alert.type}
            </Badge>
            <span className="font-semibold text-blue-900">${alert.symbol}:</span>
            <span className="ml-2 text-blue-700">{alert.content}</span>
            <span className="ml-2 text-sm text-blue-500">via {alert.source}</span>
          </div>
        ))}
      </div>
    </div>
  )
} 