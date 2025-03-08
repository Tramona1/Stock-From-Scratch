"use client"

import AnalystRatingsTable from "@/components/dashboard/AnalystRatingsTable"
import { Container } from "@/components/ui/Container"

export default function AnalystRatingsPage() {
  return (
    <Container>
      <h1 className="text-2xl font-bold mb-6">Analyst Ratings and Price Targets</h1>
      <p className="text-muted-foreground mb-6">
        Track analyst ratings, upgrades, downgrades, and price targets for the stocks in your watchlist.
        These insights can help you understand shifts in market sentiment from institutional analysts.
      </p>
      
      <AnalystRatingsTable />
    </Container>
  )
} 