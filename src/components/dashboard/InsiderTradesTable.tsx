"use client"

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, AlertTriangle, ArrowUpRight, ArrowDownRight, Filter, ChevronDown } from "lucide-react"
import { formatCurrency, formatDate } from '@/lib/utils'
import { useWatchlist } from "@/context/WatchlistContext"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"

// Initialize Supabase client
const supabase = createClient()

interface InsiderTrade {
  id: string
  symbol: string
  company_name: string
  insider_name: string
  insider_title: string
  transaction_type: string
  transaction_date: string
  shares: number
  price: number
  total_value: number
  shares_owned_after: number
  filing_date: string
}

export default function InsiderTradesTable() {
  const [trades, setTrades] = useState<InsiderTrade[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { watchlist } = useWatchlist()
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [transactionType, setTransactionType] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const itemsPerPage = 10

  // Convert watchlist items to a set of symbols for quick lookup
  const watchlistSymbols = new Set(watchlist.map(item => item.symbol))
  
  useEffect(() => {
    fetchInsiderTrades()
  }, [watchlist, currentPage, transactionType, searchQuery])

  const fetchInsiderTrades = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Only fetch insider data if we have watchlist items
      if (watchlistSymbols.size === 0) {
        setTrades([])
        setIsLoading(false)
        return
      }
      
      // Start building the query
      let query = supabase
        .from('insider_trades')
        .select('*', { count: 'exact' })
        
      // Apply watchlist filter - only show trades for stocks in the watchlist
      const watchlistArray = Array.from(watchlistSymbols)
      if (watchlistArray.length > 0) {
        query = query.in('symbol', watchlistArray)
      }
      
      // Apply transaction type filter if selected
      if (transactionType) {
        query = query.eq('transaction_type', transactionType)
      }
      
      // Apply search filter if provided
      if (searchQuery) {
        query = query.or(
          `symbol.ilike.%${searchQuery}%,company_name.ilike.%${searchQuery}%,insider_name.ilike.%${searchQuery}%`
        )
      }
      
      // Apply pagination
      const from = (currentPage - 1) * itemsPerPage
      const to = from + itemsPerPage - 1
      
      // Execute the paginated query
      const { data, error, count } = await query
        .order('transaction_date', { ascending: false })
        .range(from, to)
      
      if (error) throw error
      
      setTrades(data as InsiderTrade[])
      setTotalPages(count ? Math.ceil(count / itemsPerPage) : 1)
    } catch (err) {
      console.error('Error fetching insider trades:', err)
      setError('Failed to load insider trading data')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleTransactionFilter = (type: string | null) => {
    setTransactionType(type)
    setCurrentPage(1) // Reset to first page when changing filters
  }

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    setCurrentPage(1) // Reset to first page when searching
  }

  // Format transaction value with appropriate color
  const renderTransactionValue = (trade: InsiderTrade) => {
    const isPurchase = trade.transaction_type.toLowerCase().includes('purchase')
    const isSale = trade.transaction_type.toLowerCase().includes('sale')
    
    return (
      <div className="flex items-center">
        <span className={isPurchase ? 'text-green-600' : isSale ? 'text-red-600' : ''}>
          {formatCurrency(trade.total_value)}
        </span>
        {isPurchase && <ArrowUpRight className="ml-1 h-4 w-4 text-green-600" />}
        {isSale && <ArrowDownRight className="ml-1 h-4 w-4 text-red-600" />}
      </div>
    )
  }

  // Render transaction badge based on type
  const renderTransactionType = (type: string) => {
    if (type.toLowerCase().includes('purchase')) {
      return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Purchase</Badge>
    } else if (type.toLowerCase().includes('sale')) {
      return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Sale</Badge>
    } else {
      return <Badge variant="outline">{type}</Badge>
    }
  }

  // Render pagination controls
  const renderPagination = () => {
    return (
      <div className="flex items-center justify-between px-2 py-4">
        <Button 
          variant="outline" 
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1 || isLoading}
          size="sm"
        >
          Previous
        </Button>
        <span className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages}
        </span>
        <Button 
          variant="outline" 
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages || isLoading}
          size="sm"
        >
          Next
        </Button>
      </div>
    )
  }

  // Render filters
  const renderFilters = () => {
    return (
      <div className="flex flex-wrap gap-2 mb-4">
        <Input
          placeholder="Search by ticker, company or insider..."
          value={searchQuery}
          onChange={handleSearch}
          className="max-w-xs"
        />
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="flex items-center gap-1">
              <Filter className="h-4 w-4" />
              {transactionType ? transactionType : 'Filter by transaction'}
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => handleTransactionFilter(null)}>
              All transactions
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTransactionFilter('Purchase')}>
              Purchases only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleTransactionFilter('Sale')}>
              Sales only
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    )
  }

  // Loading skeleton
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Insider Trading Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {renderFilters()}
          <div className="space-y-4">
            {Array(5).fill(0).map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="h-4 w-[100px]" />
                <Skeleton className="h-4 w-[120px]" />
                <Skeleton className="h-4 w-[150px]" />
                <Skeleton className="h-4 w-[100px]" />
                <Skeleton className="h-4 w-[80px]" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Insider Trading Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-6">
            <AlertTriangle className="h-6 w-6 text-amber-500 mr-2" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Empty watchlist state
  if (watchlistSymbols.size === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Insider Trading Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <AlertTriangle className="h-10 w-10 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No stocks in your watchlist</h3>
            <p className="text-muted-foreground max-w-md">
              Add stocks to your watchlist to track insider trading activity. Company insiders often have valuable insights into their company's prospects.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // No data state
  if (trades.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Insider Trading Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {renderFilters()}
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <AlertTriangle className="h-10 w-10 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No insider trades found</h3>
            <p className="text-muted-foreground max-w-md">
              {searchQuery 
                ? "Try adjusting your search or filter criteria."
                : "There are no recent insider trades for your watchlisted stocks."}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Insider Trading Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {renderFilters()}
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-2 text-sm font-medium">Symbol</th>
                <th className="text-left py-3 px-2 text-sm font-medium">Insider</th>
                <th className="text-left py-3 px-2 text-sm font-medium">Title</th>
                <th className="text-left py-3 px-2 text-sm font-medium">Transaction</th>
                <th className="text-left py-3 px-2 text-sm font-medium">Date</th>
                <th className="text-right py-3 px-2 text-sm font-medium">Shares</th>
                <th className="text-right py-3 px-2 text-sm font-medium">Price</th>
                <th className="text-right py-3 px-2 text-sm font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id} className="border-b hover:bg-muted/50">
                  <td className="py-3 px-2">
                    <div className="font-medium">{trade.symbol}</div>
                    <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                      {trade.company_name}
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <div className="font-medium">{trade.insider_name}</div>
                  </td>
                  <td className="py-3 px-2">
                    <div className="text-sm text-muted-foreground truncate max-w-[150px]">
                      {trade.insider_title || '-'}
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    {renderTransactionType(trade.transaction_type)}
                  </td>
                  <td className="py-3 px-2">
                    {formatDate(new Date(trade.transaction_date))}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {trade.shares?.toLocaleString() || '-'}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {trade.price ? formatCurrency(trade.price) : '-'}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {renderTransactionValue(trade)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {renderPagination()}
      </CardContent>
    </Card>
  )
} 