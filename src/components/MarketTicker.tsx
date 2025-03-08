"use client"

import React, { useEffect, useState } from "react"

interface TickerData {
  symbol: string
  price: number
  change: string
  color: string
}

export function MarketTicker() {
  const [tickers, setTickers] = useState<TickerData[]>([
    { symbol: "SPY", price: 507.45, change: "+0.67%", color: "text-green-600" },
    { symbol: "QQQ", price: 434.67, change: "+0.89%", color: "text-green-600" },
    { symbol: "AAPL", price: 175.32, change: "+1.25%", color: "text-green-600" },
    { symbol: "MSFT", price: 416.78, change: "+0.45%", color: "text-green-600" },
    { symbol: "NVDA", price: 870.35, change: "-1.62%", color: "text-red-600" },
    { symbol: "AMZN", price: 178.12, change: "+0.78%", color: "text-green-600" },
    { symbol: "GOOGL", price: 165.43, change: "+1.32%", color: "text-green-600" },
    { symbol: "META", price: 493.56, change: "-0.42%", color: "text-red-600" },
    { symbol: "TSLA", price: 184.76, change: "-2.15%", color: "text-red-600" },
    { symbol: "BTC-USD", price: 68245.75, change: "+2.34%", color: "text-green-600" }
  ])

  return (
    <div className="bg-gradient-to-r from-blue-50 to-white py-3 overflow-hidden border-b border-blue-100">
      <div className="flex items-center animate-[marquee_30s_linear_infinite] whitespace-nowrap">
        {tickers.concat(tickers).map((ticker, i) => (
          <div key={i} className="flex items-center mx-6">
            <span className="font-semibold text-blue-900">{ticker.symbol}</span>
            <span className={`ml-2 ${ticker.color}`}>{ticker.change}</span>
          </div>
        ))}
      </div>
    </div>
  )
} 