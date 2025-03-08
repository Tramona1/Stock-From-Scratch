"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  AlertTriangle, 
  Calendar, 
  ChevronUp, 
  ChevronDown, 
  Clock, 
  Loader2, 
  RefreshCw, 
  Sparkles,
  TrendingUp,
  TrendingDown
} from "lucide-react"
import { format } from "date-fns"

// Define the earnings data type
interface EarningsData {
  symbol: string
  nextEarningsDate: string | null
  nextEarningsTime: 'before-market' | 'after-market' | 'during-market' | null
  estimatedEPS: number | null
  actualEPS: number | null
  fiscalQuarter: string | null
  fiscalYear: number | null
  analystCount: number
  surpriseHistory: Array<{
    reportDate: string
    fiscalQuarter: string
    fiscalYear: number
    estimatedEPS: number
    actualEPS: number
    surprise: number
    surprisePercentage: number
  }>
  averageSurprisePercentage: number
  priceActionHistory: Array<{
    reportDate: string
    priceChangePercent1d: number
    priceChangePercent5d: number
    priceChangePercent30d: number
    volume: number
    avgVolume: number
  }>
}

// Mock data for initial display
const mockEarningsData: EarningsData = {
  symbol: 'AAPL',
  nextEarningsDate: '2023-10-27',
  nextEarningsTime: 'after-market',
  estimatedEPS: 1.34,
  actualEPS: null,
  fiscalQuarter: 'Q4',
  fiscalYear: 2023,
  analystCount: 32,
  surpriseHistory: [
    {
      reportDate: '2023-07-28',
      fiscalQuarter: 'Q3',
      fiscalYear: 2023,
      estimatedEPS: 1.19,
      actualEPS: 1.26,
      surprise: 0.07,
      surprisePercentage: 5.88
    },
    {
      reportDate: '2023-05-04',
      fiscalQuarter: 'Q2',
      fiscalYear: 2023,
      estimatedEPS: 1.43,
      actualEPS: 1.52,
      surprise: 0.09,
      surprisePercentage: 6.29
    },
    {
      reportDate: '2023-02-02',
      fiscalQuarter: 'Q1',
      fiscalYear: 2023,
      estimatedEPS: 1.94,
      actualEPS: 1.88,
      surprise: -0.06,
      surprisePercentage: -3.09
    },
    {
      reportDate: '2022-10-27',
      fiscalQuarter: 'Q4',
      fiscalYear: 2022,
      estimatedEPS: 1.27,
      actualEPS: 1.29,
      surprise: 0.02,
      surprisePercentage: 1.57
    }
  ],
  averageSurprisePercentage: 2.66,
  priceActionHistory: [
    {
      reportDate: '2023-07-28',
      priceChangePercent1d: 2.84,
      priceChangePercent5d: 3.26,
      priceChangePercent30d: 7.45,
      volume: 98500000,
      avgVolume: 57320000
    },
    {
      reportDate: '2023-05-04',
      priceChangePercent1d: 4.69,
      priceChangePercent5d: 6.22,
      priceChangePercent30d: 9.88,
      volume: 112450000,
      avgVolume: 62150000
    },
    {
      reportDate: '2023-02-02',
      priceChangePercent1d: -3.22,
      priceChangePercent5d: 4.15,
      priceChangePercent30d: 8.65,
      volume: 143750000,
      avgVolume: 71420000
    },
    {
      reportDate: '2022-10-27',
      priceChangePercent1d: -2.45,
      priceChangePercent5d: -1.38,
      priceChangePercent30d: 2.76,
      volume: 106280000,
      avgVolume: 68350000
    }
  ]
};

// Format volume numbers
function formatVolume(num: number): string {
  if (num >= 1_000_000_000) {
    return `${(num / 1_000_000_000).toFixed(2)}B`;
  } else if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2)}M`;
  } else if (num >= 1_000) {
    return `${(num / 1_000).toFixed(2)}K`;
  }
  return num.toString();
}

// Format date in a readable format
function formatDate(dateString: string | null): string {
  if (!dateString) return 'Unknown';
  try {
    const date = new Date(dateString);
    return format(date, 'MMM d, yyyy');
  } catch (e) {
    return 'Invalid date';
  }
}

// Calculate days until earnings
function daysUntilEarnings(dateString: string | null): string {
  if (!dateString) return 'Unknown';
  try {
    const earningsDate = new Date(dateString);
    const today = new Date();
    
    // Reset time portion for accurate day calculation
    earningsDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    
    const diffTime = earningsDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays < 0) return 'Past';
    
    return `In ${diffDays} days`;
  } catch (e) {
    return 'Unknown';
  }
}

interface EarningsCardProps {
  ticker?: string;
}

export function EarningsCard({ ticker = 'AAPL' }: EarningsCardProps) {
  const [earningsData, setEarningsData] = useState<EarningsData | null>(mockEarningsData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('upcoming');
  
  // Fetch earnings data (to be implemented with real API later)
  const fetchEarningsData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // This will be replaced with actual API call later
      // const response = await fetch(`/api/earnings/${ticker}`);
      // const data = await response.json();
      // setEarningsData(data);
      
      // For now, just simulate an API call
      setTimeout(() => {
        setEarningsData(mockEarningsData);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Error fetching earnings data:', err);
      setError('Failed to load earnings data');
      setIsLoading(false);
    }
  };
  
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  if (error || !earningsData) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <CardTitle className="mb-2">Failed to Load Earnings Data</CardTitle>
          <CardDescription className="mb-4">
            {error || 'Earnings data is currently unavailable'}
          </CardDescription>
          <Button onClick={fetchEarningsData}>Retry</Button>
        </CardContent>
      </Card>
    );
  }
  
  const earningsTimeLabel = earningsData.nextEarningsTime === 'before-market'
    ? 'Before Market Open'
    : earningsData.nextEarningsTime === 'after-market'
    ? 'After Market Close'
    : earningsData.nextEarningsTime === 'during-market'
    ? 'During Market Hours'
    : 'Unknown';
  
  const daysUntil = daysUntilEarnings(earningsData.nextEarningsDate);
  const isUpcoming = daysUntil !== 'Past';
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Earnings Information
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchEarningsData}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      
      <Tabs defaultValue="upcoming" value={activeTab} onValueChange={setActiveTab}>
        <div className="px-6">
          <TabsList className="w-full">
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="history">Surprise History</TabsTrigger>
            <TabsTrigger value="price-action">Price Action</TabsTrigger>
          </TabsList>
        </div>
        
        <CardContent className="p-6 pt-4">
          <TabsContent value="upcoming" className="m-0">
            <div className="space-y-4">
              {isUpcoming && earningsData.nextEarningsDate ? (
                <div className="bg-muted/50 p-4 rounded-md border border-primary/20">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-medium mb-1">Next Earnings Report</h3>
                      <div className="text-sm text-muted-foreground">
                        {earningsData.fiscalQuarter} {earningsData.fiscalYear}
                      </div>
                    </div>
                    <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {daysUntil}
                    </Badge>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Date</div>
                      <div className="font-medium flex items-center">
                        <Calendar className="h-3 w-3 mr-1 text-muted-foreground" />
                        {formatDate(earningsData.nextEarningsDate)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Time</div>
                      <div className="font-medium flex items-center">
                        <Clock className="h-3 w-3 mr-1 text-muted-foreground" />
                        {earningsTimeLabel}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Estimated EPS</div>
                      <div className="font-medium">
                        ${earningsData.estimatedEPS?.toFixed(2) || 'Unknown'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Analyst Coverage</div>
                      <div className="font-medium">
                        {earningsData.analystCount} analysts
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-muted/50 p-4 rounded-md text-center">
                  <p className="text-muted-foreground">No upcoming earnings announcement found.</p>
                </div>
              )}
              
              <div className="bg-muted/50 p-4 rounded-md">
                <h3 className="text-sm font-medium mb-2">Past Performance</h3>
                <div className="space-y-1">
                  <div className="flex justify-between items-center text-sm">
                    <span>Avg. Surprise:</span>
                    <span className={earningsData.averageSurprisePercentage >= 0 ? "text-green-500" : "text-red-500"}>
                      {earningsData.averageSurprisePercentage >= 0 ? "+" : ""}
                      {earningsData.averageSurprisePercentage.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span>Beat Expectations:</span>
                    <span>
                      {earningsData.surpriseHistory.filter(h => h.surprisePercentage > 0).length} of last {earningsData.surpriseHistory.length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span>Missed Expectations:</span>
                    <span>
                      {earningsData.surpriseHistory.filter(h => h.surprisePercentage < 0).length} of last {earningsData.surpriseHistory.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="history" className="m-0">
            <div className="space-y-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <h3 className="text-sm font-medium mb-2">Earnings Surprise History</h3>
                {earningsData.surpriseHistory.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-muted-foreground border-b">
                          <th className="pb-2 text-left font-medium">Quarter</th>
                          <th className="pb-2 text-left font-medium">Date</th>
                          <th className="pb-2 text-right font-medium">Est. EPS</th>
                          <th className="pb-2 text-right font-medium">Actual EPS</th>
                          <th className="pb-2 text-right font-medium">Surprise</th>
                        </tr>
                      </thead>
                      <tbody>
                        {earningsData.surpriseHistory.map((item, index) => (
                          <tr key={index} className="border-b last:border-b-0 border-border/50">
                            <td className="py-2 text-left">
                              {item.fiscalQuarter} {item.fiscalYear}
                            </td>
                            <td className="py-2 text-left">
                              {formatDate(item.reportDate)}
                            </td>
                            <td className="py-2 text-right">
                              ${item.estimatedEPS.toFixed(2)}
                            </td>
                            <td className="py-2 text-right">
                              ${item.actualEPS.toFixed(2)}
                            </td>
                            <td className="py-2 text-right">
                              <div className="flex items-center justify-end">
                                {item.surprisePercentage > 0 ? (
                                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 flex items-center">
                                    <ChevronUp className="h-3 w-3 mr-0.5" />
                                    {item.surprisePercentage.toFixed(2)}%
                                  </Badge>
                                ) : item.surprisePercentage < 0 ? (
                                  <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 flex items-center">
                                    <ChevronDown className="h-3 w-3 mr-0.5" />
                                    {Math.abs(item.surprisePercentage).toFixed(2)}%
                                  </Badge>
                                ) : (
                                  <Badge variant="outline">0.00%</Badge>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground p-4">
                    No earnings history available
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="price-action" className="m-0">
            <div className="space-y-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <h3 className="text-sm font-medium mb-2">Post-Earnings Price Action</h3>
                {earningsData.priceActionHistory.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-muted-foreground border-b">
                          <th className="pb-2 text-left font-medium">Report Date</th>
                          <th className="pb-2 text-right font-medium">1 Day</th>
                          <th className="pb-2 text-right font-medium">5 Days</th>
                          <th className="pb-2 text-right font-medium">30 Days</th>
                          <th className="pb-2 text-right font-medium">Volume</th>
                        </tr>
                      </thead>
                      <tbody>
                        {earningsData.priceActionHistory.map((item, index) => (
                          <tr key={index} className="border-b last:border-b-0 border-border/50">
                            <td className="py-2 text-left">
                              {formatDate(item.reportDate)}
                            </td>
                            <td className="py-2 text-right">
                              <span className={item.priceChangePercent1d > 0 ? "text-green-500" : item.priceChangePercent1d < 0 ? "text-red-500" : ""}>
                                {item.priceChangePercent1d > 0 ? "+" : ""}
                                {item.priceChangePercent1d.toFixed(2)}%
                              </span>
                            </td>
                            <td className="py-2 text-right">
                              <span className={item.priceChangePercent5d > 0 ? "text-green-500" : item.priceChangePercent5d < 0 ? "text-red-500" : ""}>
                                {item.priceChangePercent5d > 0 ? "+" : ""}
                                {item.priceChangePercent5d.toFixed(2)}%
                              </span>
                            </td>
                            <td className="py-2 text-right">
                              <span className={item.priceChangePercent30d > 0 ? "text-green-500" : item.priceChangePercent30d < 0 ? "text-red-500" : ""}>
                                {item.priceChangePercent30d > 0 ? "+" : ""}
                                {item.priceChangePercent30d.toFixed(2)}%
                              </span>
                            </td>
                            <td className="py-2 text-right">
                              <div className="flex items-center justify-end">
                                {formatVolume(item.volume)}
                                {item.volume > item.avgVolume * 1.5 && (
                                  <Badge className="ml-1 px-1 py-0 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 flex items-center">
                                    <Sparkles className="h-2 w-2 mr-0.5" />
                                    High
                                  </Badge>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground p-4">
                    No price action history available
                  </div>
                )}
              </div>
              
              <div className="bg-muted/50 p-3 rounded-md">
                <h3 className="text-sm font-medium mb-1">Price Trends After Earnings</h3>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">1 Day</div>
                    <div className="flex items-center">
                      {earningsData.priceActionHistory.filter(item => item.priceChangePercent1d > 0).length > 
                       earningsData.priceActionHistory.filter(item => item.priceChangePercent1d < 0).length ? (
                        <><TrendingUp className="h-3 w-3 text-green-500 mr-1" /> <span className="text-green-500">Usually Up</span></>
                      ) : (
                        <><TrendingDown className="h-3 w-3 text-red-500 mr-1" /> <span className="text-red-500">Usually Down</span></>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">5 Days</div>
                    <div className="flex items-center">
                      {earningsData.priceActionHistory.filter(item => item.priceChangePercent5d > 0).length > 
                       earningsData.priceActionHistory.filter(item => item.priceChangePercent5d < 0).length ? (
                        <><TrendingUp className="h-3 w-3 text-green-500 mr-1" /> <span className="text-green-500">Usually Up</span></>
                      ) : (
                        <><TrendingDown className="h-3 w-3 text-red-500 mr-1" /> <span className="text-red-500">Usually Down</span></>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">30 Days</div>
                    <div className="flex items-center">
                      {earningsData.priceActionHistory.filter(item => item.priceChangePercent30d > 0).length > 
                       earningsData.priceActionHistory.filter(item => item.priceChangePercent30d < 0).length ? (
                        <><TrendingUp className="h-3 w-3 text-green-500 mr-1" /> <span className="text-green-500">Usually Up</span></>
                      ) : (
                        <><TrendingDown className="h-3 w-3 text-red-500 mr-1" /> <span className="text-red-500">Usually Down</span></>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </CardContent>
      </Tabs>
      
      <CardFooter className="text-xs text-muted-foreground border-t pt-4">
        <div className="flex items-center">
          <span className="mr-auto">Based on historical earnings data</span>
          <span>Updated daily</span>
        </div>
      </CardFooter>
    </Card>
  );
} 