"use client"

import * as React from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function TickerInput() {
  const [search, setSearch] = React.useState("")

  return (
    <div className="relative flex w-full max-w-sm items-center">
      <Input
        type="search"
        placeholder="Enter ticker symbol..."
        className="pr-12"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <Button 
        size="sm" 
        variant="ghost" 
        className="absolute right-0 top-0 h-full px-3"
      >
        <Search className="h-4 w-4" />
      </Button>
    </div>
  )
} 