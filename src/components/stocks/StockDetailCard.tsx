"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { 
  BarChart3, 
  Building, 
  Calendar, 
  ExternalLink, 
  Globe, 
  Info, 
  Loader2, 
  Maximize, 
  TrendingDown, 
  TrendingUp, 
  Users,
  Briefcase,
  Landmark,
  DollarSign,
  BarChart,
  Target
} from "lucide-react"
import Image from 'next/image'

// Define the stock detail type
interface StockDetail {
  ticker: string
  companyName: string
  shortName?: string
  logoUrl?: string
  sector?: string
  industry?: string
  description?: string
  currentPrice: number
  previousClose: number
  change: number
  changePercent: number
  marketCap?: number
  peRatio?: number
  dividendYield?: number
  beta?: number
  fiftyTwoWeekHigh?: number
  fiftyTwoWeekLow?: number
  avgVolume?: number
  volume?: number
  sharesOutstanding?: number
  float?: number
  exchange?: string
  ceo?: string
  founded?: number
  employees?: number
  headquarters?: string
  website?: string
  hasOptions?: boolean
  hasDividend?: boolean
  nextEarningsDate?: string
  earningsAnnounceTime?: string
}

// Helper functions for formatting
function formatLargeNumber(num?: number): string {
  if (num === undefined || num === null) return 'N/A';
  
  if (num >= 1_000_000_000_000) {
    return `$${(num / 1_000_000_000_000).toFixed(2)}T`;
  } else if (num >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(2)}B`;
  } else if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(2)}M`;
  } else if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(2)}K`;
  }
  return `$${num.toFixed(2)}`;
}

function formatVolume(num?: number): string {
  if (num === undefined || num === null) return 'N/A';
  
  if (num >= 1_000_000_000) {
    return `${(num / 1_000_000_000).toFixed(2)}B`;
  } else if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2)}M`;
  } else if (num >= 1_000) {
    return `${(num / 1_000).toFixed(2)}K`;
  }
  return num.toString();
}

// Mock data for initial display
const mockStockDetail: StockDetail = {
  ticker: 'AAPL',
  companyName: 'Apple Inc.',
  shortName: 'Apple',
  logoUrl: 'https://logo.clearbit.com/apple.com',
  sector: 'Technology',
  industry: 'Consumer Electronics',
  description: 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. It also sells various related services. The company offers iPhone, a line of smartphones.',
  currentPrice: 182.63,
  previousClose: 181.14,
  change: 1.49,
  changePercent: 0.82,
  marketCap: 2870000000000,
  peRatio: 30.15,
  dividendYield: 0.51,
  beta: 1.28,
  fiftyTwoWeekHigh: 199.62,
  fiftyTwoWeekLow: 142.45,
  avgVolume: 58250000,
  volume: 47840000,
  sharesOutstanding: 15700000000,
  float: 15680000000,
  exchange: 'NASDAQ',
  ceo: 'Tim Cook',
  founded: 1976,
  employees: 164000,
  headquarters: 'Cupertino, CA',
  website: 'https://www.apple.com',
  hasOptions: true,
  hasDividend: true,
  nextEarningsDate: '2023-10-26',
  earningsAnnounceTime: 'After Market Close'
};

interface StockDetailCardProps {
  ticker?: string;
  isDialog?: boolean;
  onClose?: () => void;
}

export function StockDetailCard({ ticker = 'AAPL', isDialog = false, onClose }: StockDetailCardProps) {
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(mockStockDetail);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch stock details (to be implemented with real API later)
  const fetchStockDetail = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // This will be replaced with actual API call later
      // const response = await fetch(`/api/stocks/${ticker}`);
      // const data = await response.json();
      // setStockDetail(data);
      
      // For now, just simulate an API call
      setTimeout(() => {
        setStockDetail(mockStockDetail);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Error fetching stock details:', err);
      setError('Failed to load stock details');
      setIsLoading(false);
    }
  };
  
  if (isLoading) {
    return (
      <Card className={isDialog ? '' : 'h-full'}>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  if (error || !stockDetail) {
    return (
      <Card className={isDialog ? '' : 'h-full'}>
        <CardContent className="py-8 text-center">
          <Info className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <CardTitle className="mb-2">Failed to Load Stock Details</CardTitle>
          <CardDescription className="mb-4">
            {error || 'Stock information is currently unavailable'}
          </CardDescription>
          <Button onClick={fetchStockDetail}>Retry</Button>
        </CardContent>
      </Card>
    );
  }
  
  const isPositive = stockDetail.change > 0;
  const formattedDate = stockDetail.nextEarningsDate 
    ? new Date(stockDetail.nextEarningsDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric'
      })
    : 'N/A';
  
  return (
    <Card className={isDialog ? '' : 'h-full'}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            {stockDetail.logoUrl && (
              <div className="relative h-10 w-10 mr-3 border rounded overflow-hidden">
                {/* We'll replace with Image component for production */}
                <img 
                  src={stockDetail.logoUrl} 
                  alt={`${stockDetail.companyName} logo`}
                  className="object-contain"
                />
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <CardTitle>{stockDetail.ticker}</CardTitle>
                <Badge variant="outline" className="text-xs px-1 py-0 h-5">
                  {stockDetail.exchange}
                </Badge>
              </div>
              <CardDescription className="text-base mt-0.5">
                {stockDetail.companyName}
              </CardDescription>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold">${stockDetail.currentPrice.toFixed(2)}</div>
            <div className={isPositive ? "text-green-500 flex items-center justify-end" : "text-red-500 flex items-center justify-end"}>
              {isPositive ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
              {isPositive ? '+' : ''}{stockDetail.change.toFixed(2)} ({stockDetail.changePercent.toFixed(2)}%)
            </div>
          </div>
        </div>
      </CardHeader>
      
      <Separator />
      
      <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full justify-start px-6 pt-2">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="financials">Financials</TabsTrigger>
          <TabsTrigger value="company">Company</TabsTrigger>
        </TabsList>
        
        <CardContent className="pt-4 pb-6">
          <TabsContent value="overview" className="m-0">
            {stockDetail.description && (
              <div className="mb-4">
                <p className="text-sm text-muted-foreground">{stockDetail.description}</p>
              </div>
            )}
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <BarChart3 className="h-3 w-3 mr-1" />
                  Sector
                </div>
                <div className="font-medium">{stockDetail.sector || 'N/A'}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Briefcase className="h-3 w-3 mr-1" />
                  Industry
                </div>
                <div className="font-medium">{stockDetail.industry || 'N/A'}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Calendar className="h-3 w-3 mr-1" />
                  Next Earnings
                </div>
                <div className="font-medium">
                  {formattedDate}
                  {stockDetail.earningsAnnounceTime && (
                    <span className="text-xs ml-1 text-muted-foreground">
                      ({stockDetail.earningsAnnounceTime})
                    </span>
                  )}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Maximize className="h-3 w-3 mr-1" />
                  52-Week Range
                </div>
                <div className="font-medium">
                  ${stockDetail.fiftyTwoWeekLow?.toFixed(2) || 'N/A'} - ${stockDetail.fiftyTwoWeekHigh?.toFixed(2) || 'N/A'}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <BarChart className="h-3 w-3 mr-1" />
                  Volume
                </div>
                <div className="font-medium">
                  {formatVolume(stockDetail.volume)}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <BarChart className="h-3 w-3 mr-1" />
                  Avg. Volume
                </div>
                <div className="font-medium">
                  {formatVolume(stockDetail.avgVolume)}
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="financials" className="m-0">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Landmark className="h-3 w-3 mr-1" />
                  Market Cap
                </div>
                <div className="font-medium">{formatLargeNumber(stockDetail.marketCap)}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Target className="h-3 w-3 mr-1" />
                  P/E Ratio
                </div>
                <div className="font-medium">{stockDetail.peRatio?.toFixed(2) || 'N/A'}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <DollarSign className="h-3 w-3 mr-1" />
                  Dividend Yield
                </div>
                <div className="font-medium">
                  {stockDetail.dividendYield 
                    ? `${(stockDetail.dividendYield * 100).toFixed(2)}%` 
                    : 'N/A'}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  Beta
                </div>
                <div className="font-medium">{stockDetail.beta?.toFixed(2) || 'N/A'}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Info className="h-3 w-3 mr-1" />
                  Shares Outstanding
                </div>
                <div className="font-medium">
                  {stockDetail.sharesOutstanding 
                    ? formatVolume(stockDetail.sharesOutstanding) 
                    : 'N/A'}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Info className="h-3 w-3 mr-1" />
                  Float
                </div>
                <div className="font-medium">
                  {stockDetail.float 
                    ? formatVolume(stockDetail.float) 
                    : 'N/A'}
                </div>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-6">
              {stockDetail.hasDividend && (
                <Badge variant="outline" className="bg-green-50 dark:bg-green-950">
                  Pays Dividend
                </Badge>
              )}
              {stockDetail.hasOptions && (
                <Badge variant="outline" className="bg-blue-50 dark:bg-blue-950">
                  Has Options
                </Badge>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="company" className="m-0">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Building className="h-3 w-3 mr-1" />
                  Headquarters
                </div>
                <div className="font-medium">{stockDetail.headquarters || 'N/A'}</div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Users className="h-3 w-3 mr-1" />
                  Employees
                </div>
                <div className="font-medium">
                  {stockDetail.employees 
                    ? stockDetail.employees.toLocaleString() 
                    : 'N/A'}
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Calendar className="h-3 w-3 mr-1" />
                  Founded
                </div>
                <div className="font-medium">{stockDetail.founded || 'N/A'}</div>
              </div>
              
              <div className="space-y-1 col-span-3">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Globe className="h-3 w-3 mr-1" />
                  Website
                </div>
                <div className="font-medium">
                  {stockDetail.website ? (
                    <a 
                      href={stockDetail.website} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center"
                    >
                      {stockDetail.website}
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  ) : 'N/A'}
                </div>
              </div>
              
              <div className="space-y-1 col-span-3">
                <div className="text-xs text-muted-foreground flex items-center">
                  <Users className="h-3 w-3 mr-1" />
                  CEO
                </div>
                <div className="font-medium">{stockDetail.ceo || 'N/A'}</div>
              </div>
            </div>
          </TabsContent>
        </CardContent>
      </Tabs>
      
      {isDialog && (
        <CardFooter className="flex justify-between border-t pt-4">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button variant="outline" onClick={() => window.open(`https://finance.yahoo.com/quote/${stockDetail.ticker}`, '_blank')}>
            View on Yahoo Finance
            <ExternalLink className="h-3 w-3 ml-1" />
          </Button>
        </CardFooter>
      )}
    </Card>
  );
} 