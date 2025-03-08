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

interface AnalystRating {
  id: string
  symbol: string
  company_name: string
  analyst_firm: string
  analyst_name: string | null
  rating: string
  rating_prior: string | null
  rating_action: string
  price_target: number
  price_target_prior: number | null
  price_target_change: number | null
  price_target_change_percent: number | null
  rating_date: string
}

export default function AnalystRatingsTable() {
  const [ratings, setRatings] = useState<AnalystRating[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { watchlist } = useWatchlist()
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [ratingAction, setRatingAction] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const itemsPerPage = 10

  // Convert watchlist items to a set of symbols for quick lookup
  const watchlistSymbols = new Set(watchlist.map(item => item.symbol))
  
  useEffect(() => {
    fetchAnalystRatings()
  }, [watchlist, currentPage, ratingAction, searchQuery])

  const fetchAnalystRatings = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Only fetch analyst ratings data if we have watchlist items
      if (watchlistSymbols.size === 0) {
        setRatings([])
        setIsLoading(false)
        return
      }
      
      // Start building the query
      let query = supabase
        .from('analyst_ratings')
        .select('*', { count: 'exact' })
        
      // Apply watchlist filter - only show ratings for stocks in the watchlist
      const watchlistArray = Array.from(watchlistSymbols)
      if (watchlistArray.length > 0) {
        query = query.in('symbol', watchlistArray)
      }
      
      // Apply rating action filter if selected
      if (ratingAction) {
        query = query.eq('rating_action', ratingAction)
      }
      
      // Apply search filter if provided
      if (searchQuery) {
        query = query.or(
          `symbol.ilike.%${searchQuery}%,company_name.ilike.%${searchQuery}%,analyst_firm.ilike.%${searchQuery}%`
        )
      }
      
      // Apply pagination
      const from = (currentPage - 1) * itemsPerPage
      const to = from + itemsPerPage - 1
      
      // Execute the paginated query
      const { data, error, count } = await query
        .order('rating_date', { ascending: false })
        .range(from, to)
      
      if (error) throw error
      
      setRatings(data as AnalystRating[])
      setTotalPages(count ? Math.ceil(count / itemsPerPage) : 1)
    } catch (err) {
      console.error('Error fetching analyst ratings:', err)
      setError('Failed to load analyst ratings data')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleRatingFilter = (action: string | null) => {
    setRatingAction(action)
    setCurrentPage(1) // Reset to first page when changing filters
  }

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    setCurrentPage(1) // Reset to first page when searching
  }

  // Format price target change with appropriate color
  const renderPriceTargetChange = (rating: AnalystRating) => {
    if (rating.price_target_change_percent === null) return 'N/A'
    
    const isPositive = rating.price_target_change_percent > 0
    const isNegative = rating.price_target_change_percent < 0
    
    return (
      <div className="flex items-center">
        <span className={isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : ''}>
          {rating.price_target_change_percent > 0 ? '+' : ''}
          {rating.price_target_change_percent.toFixed(2)}%
        </span>
        {isPositive && <ArrowUpRight className="ml-1 h-4 w-4 text-green-600" />}
        {isNegative && <ArrowDownRight className="ml-1 h-4 w-4 text-red-600" />}
      </div>
    )
  }

  // Render rating badge based on action
  const renderRatingBadge = (action: string) => {
    if (action.toLowerCase().includes('upgrade')) {
      return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Upgrade</Badge>
    } else if (action.toLowerCase().includes('downgrade')) {
      return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Downgrade</Badge>
    } else if (action.toLowerCase().includes('initiate') || action.toLowerCase().includes('coverage')) {
      return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">New Coverage</Badge>
    } else {
      return <Badge variant="outline">{action}</Badge>
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
          placeholder="Search by ticker, company or analyst firm..."
          value={searchQuery}
          onChange={handleSearch}
          className="max-w-xs"
        />
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="flex items-center gap-1">
              <Filter className="h-4 w-4" />
              {ratingAction ? ratingAction : 'Filter by action'}
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => handleRatingFilter(null)}>
              All actions
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleRatingFilter('Upgrade')}>
              Upgrades only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleRatingFilter('Downgrade')}>
              Downgrades only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleRatingFilter('Initiated Coverage')}>
              New coverage only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleRatingFilter('Reiterated')}>
              Reiterations only
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
          <CardTitle className="text-xl">Analyst Ratings</CardTitle>
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

  // Empty watchlist state
  if (watchlist.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Analyst Ratings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <AlertTriangle className="h-8 w-8 text-amber-500 mb-4" />
            <h3 className="text-lg font-medium">No stocks in your watchlist</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Add stocks to your watchlist to see analyst ratings and price targets.
            </p>
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
          <CardTitle className="text-xl">Analyst Ratings</CardTitle>
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

  // Empty results state
  if (ratings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Analyst Ratings</CardTitle>
        </CardHeader>
        <CardContent>
          {renderFilters()}
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <AlertTriangle className="h-8 w-8 text-amber-500 mb-4" />
            <h3 className="text-lg font-medium">No analyst ratings found</h3>
            <p className="text-sm text-muted-foreground mt-2">
              {searchQuery || ratingAction 
                ? "Try adjusting your filters or search criteria."
                : "No recent analyst ratings for your watchlist stocks."}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Analyst Ratings</CardTitle>
      </CardHeader>
      <CardContent>
        {renderFilters()}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="py-2 px-2 text-left font-medium text-sm">Date</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Stock</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Firm</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Action</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Rating</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Price Target</th>
                <th className="py-2 px-2 text-left font-medium text-sm">Change</th>
              </tr>
            </thead>
            <tbody>
              {ratings.map((rating) => (
                <tr key={rating.id} className="border-b hover:bg-muted/50">
                  <td className="py-2 px-2 text-sm">
                    {new Date(rating.rating_date).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-2 text-sm font-medium">
                    {rating.symbol}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    {rating.analyst_firm}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    {renderRatingBadge(rating.rating_action)}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    {rating.rating}
                    {rating.rating_prior && (
                      <span className="text-muted-foreground ml-1 text-xs">
                        (from {rating.rating_prior})
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    ${rating.price_target.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    {renderPriceTargetChange(rating)}
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