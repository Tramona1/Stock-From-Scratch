"use client"

import { default as InsiderTradesTable } from "@/components/dashboard/InsiderTradesTable"
import { Container } from "@/components/ui/Container"

export default function InsiderTradingPage() {
  return (
    <Container>
      <h1 className="text-2xl font-bold mb-6">Insider Trading Activity</h1>
      <p className="text-muted-foreground mb-6">
        Track insider trading activity for the stocks in your watchlist. Company insiders often have valuable insights into their company's future.
      </p>
      
      <InsiderTradesTable />
    </Container>
  )
} 