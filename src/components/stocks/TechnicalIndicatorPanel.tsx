"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { 
  AlertTriangle, 
  BarChart, 
  BarChart2, 
  BarChart4,
  ChevronUp, 
  ChevronDown, 
  Clock, 
  LineChart, 
  Loader2, 
  Minus, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  Zap
} from "lucide-react"
import { Progress } from "@/components/ui/progress"

// Define the technical indicators type
interface TechnicalIndicator {
  symbol: string
  date: string
  interval: string
  indicators: {
    rsi: {
      current: number
      previous: number
      signal: 'overbought' | 'oversold' | 'neutral'
    }
    macd: {
      value: number
      signal: number
      histogram: number
      trend: 'bullish' | 'bearish' | 'neutral'
    }
    bollinger: {
      upper: number
      middle: number
      lower: number
      width: number
      percentB: number
      signal: 'upper_touch' | 'lower_touch' | 'middle_cross' | 'neutral'
    }
    movingAverages: {
      sma20: number
      sma50: number
      sma200: number
      ema9: number
      ema21: number
      signal: 'golden_cross' | 'death_cross' | 'above_all' | 'below_all' | 'mixed'
    }
    volume: {
      current: number
      average: number
      ratio: number
      trend: 'increasing' | 'decreasing' | 'stable'
    }
    support: number
    resistance: number
    lastUpdated: string
  }
}

// Mock data for initial display
const mockIndicators: TechnicalIndicator = {
  symbol: 'AAPL',
  date: '2023-08-16',
  interval: 'daily',
  indicators: {
    rsi: {
      current: 62.3,
      previous: 59.8,
      signal: 'neutral'
    },
    macd: {
      value: 0.85,
      signal: 0.62,
      histogram: 0.23,
      trend: 'bullish'
    },
    bollinger: {
      upper: 188.42,
      middle: 181.27,
      lower: 174.12,
      width: 7.9,
      percentB: 0.65,
      signal: 'neutral'
    },
    movingAverages: {
      sma20: 179.84,
      sma50: 175.62,
      sma200: 168.45,
      ema9: 182.10,
      ema21: 180.15,
      signal: 'above_all'
    },
    volume: {
      current: 47840000,
      average: 58250000,
      ratio: 0.82,
      trend: 'decreasing'
    },
    support: 178.50,
    resistance: 185.75,
    lastUpdated: '2023-08-16T16:30:00Z'
  }
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

// Format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffHours > 0) {
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
  } else if (diffMins > 0) {
    return diffMins === 1 ? '1 minute ago' : `${diffMins} minutes ago`;
  } else {
    return 'Just now';
  }
}

interface TechnicalIndicatorPanelProps {
  ticker?: string;
  interval?: string;
}

export function TechnicalIndicatorPanel({ ticker = 'AAPL', interval = 'daily' }: TechnicalIndicatorPanelProps) {
  const [indicators, setIndicators] = useState<TechnicalIndicator | null>(mockIndicators);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('summary');
  
  // Fetch technical indicators (to be implemented with real API later)
  const fetchIndicators = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // This will be replaced with actual API call later
      // const response = await fetch(`/api/indicators/${ticker}?interval=${interval}`);
      // const data = await response.json();
      // setIndicators(data);
      
      // For now, just simulate an API call
      setTimeout(() => {
        setIndicators(mockIndicators);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Error fetching technical indicators:', err);
      setError('Failed to load technical indicators');
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
  
  if (error || !indicators) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <CardTitle className="mb-2">Failed to Load Technical Indicators</CardTitle>
          <CardDescription className="mb-4">
            {error || 'Technical indicator data is currently unavailable'}
          </CardDescription>
          <Button onClick={fetchIndicators}>Retry</Button>
        </CardContent>
      </Card>
    );
  }
  
  const lastUpdated = formatRelativeTime(indicators.indicators.lastUpdated);
  
  // Get signal badges
  const getSignalBadge = (type: string, value: string) => {
    if (type === 'rsi') {
      if (value === 'overbought') return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Overbought</Badge>;
      if (value === 'oversold') return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Oversold</Badge>;
      return <Badge variant="outline">Neutral</Badge>;
    }
    
    if (type === 'macd') {
      if (value === 'bullish') return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Bullish</Badge>;
      if (value === 'bearish') return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Bearish</Badge>;
      return <Badge variant="outline">Neutral</Badge>;
    }
    
    if (type === 'movingAverages') {
      if (value === 'golden_cross') return <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Golden Cross</Badge>;
      if (value === 'death_cross') return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Death Cross</Badge>;
      if (value === 'above_all') return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Above All MAs</Badge>;
      if (value === 'below_all') return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Below All MAs</Badge>;
      return <Badge variant="outline">Mixed Signals</Badge>;
    }
    
    if (type === 'volume') {
      if (value === 'increasing') return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">Increasing</Badge>;
      if (value === 'decreasing') return <Badge className="bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">Decreasing</Badge>;
      return <Badge variant="outline">Stable</Badge>;
    }
    
    return <Badge variant="outline">{value}</Badge>;
  };
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2">
          <BarChart className="h-5 w-5" />
          Technical Analysis
          <Badge variant="outline">{indicators.interval}</Badge>
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchIndicators}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      
      <Tabs defaultValue="summary" value={activeTab} onValueChange={setActiveTab}>
        <div className="px-6">
          <TabsList className="w-full">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="oscillators">Oscillators</TabsTrigger>
            <TabsTrigger value="moving-averages">Moving Averages</TabsTrigger>
          </TabsList>
        </div>
        
        <CardContent className="p-6 pt-4">
          <TabsContent value="summary" className="m-0">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-4">
                <div className="bg-muted/50 p-3 rounded-md">
                  <div className="flex justify-between items-center mb-1">
                    <h4 className="font-medium">RSI (14)</h4>
                    {getSignalBadge('rsi', indicators.indicators.rsi.signal)}
                  </div>
                  <div className="relative pt-1">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Oversold</span>
                      <span>Neutral</span>
                      <span>Overbought</span>
                    </div>
                    <div className="flex h-2 overflow-hidden text-xs rounded bg-secondary">
                      <div className="bg-green-500 rounded-l" style={{ width: '30%' }}></div>
                      <div className="bg-secondary" style={{ width: '40%' }}></div>
                      <div className="bg-red-500 rounded-r" style={{ width: '30%' }}></div>
                    </div>
                    <div 
                      className="absolute w-2 h-3 bg-primary bottom-0 -mb-0.5 transform -translate-x-1/2 rounded"
                      style={{ left: `${indicators.indicators.rsi.current}%` }}
                    ></div>
                    <div className="mt-2 text-sm font-semibold">
                      {indicators.indicators.rsi.current}
                      <span className="text-xs ml-1 text-muted-foreground">
                        ({indicators.indicators.rsi.current > indicators.indicators.rsi.previous ? '+' : ''}
                        {(indicators.indicators.rsi.current - indicators.indicators.rsi.previous).toFixed(1)})
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-muted/50 p-3 rounded-md">
                  <div className="flex justify-between items-center mb-1">
                    <h4 className="font-medium">MACD (12,26,9)</h4>
                    {getSignalBadge('macd', indicators.indicators.macd.trend)}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">MACD Line</div>
                      <div className={indicators.indicators.macd.value >= 0 ? "text-green-500" : "text-red-500"}>
                        {indicators.indicators.macd.value.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Signal Line</div>
                      <div>{indicators.indicators.macd.signal.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Histogram</div>
                      <div className={indicators.indicators.macd.histogram >= 0 ? "text-green-500 flex items-center" : "text-red-500 flex items-center"}>
                        {indicators.indicators.macd.histogram >= 0 ? <ChevronUp className="h-3 w-3 mr-1" /> : <ChevronDown className="h-3 w-3 mr-1" />}
                        {Math.abs(indicators.indicators.macd.histogram).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-muted/50 p-3 rounded-md">
                  <div className="flex justify-between items-center mb-1">
                    <h4 className="font-medium">Bollinger Bands</h4>
                    <div className="text-xs text-muted-foreground">Width: {indicators.indicators.bollinger.width.toFixed(1)}</div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">Upper Band</div>
                      <div>${indicators.indicators.bollinger.upper.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Middle Band</div>
                      <div>${indicators.indicators.bollinger.middle.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Lower Band</div>
                      <div>${indicators.indicators.bollinger.lower.toFixed(2)}</div>
                    </div>
                  </div>
                  <div className="mt-1">
                    <div className="text-xs text-muted-foreground">%B</div>
                    <Progress value={indicators.indicators.bollinger.percentB * 100} className="h-2" />
                    <div className="text-right text-xs mt-1">
                      {(indicators.indicators.bollinger.percentB * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                
                <div className="bg-muted/50 p-3 rounded-md">
                  <div className="flex justify-between items-center mb-1">
                    <h4 className="font-medium">Support & Resistance</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">Resistance</div>
                      <div className="text-red-500">${indicators.indicators.resistance.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Support</div>
                      <div className="text-green-500">${indicators.indicators.support.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-4 text-xs text-muted-foreground flex items-center justify-between">
              <span className="flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                Last updated {lastUpdated}
              </span>
              <span>Interval: {indicators.interval}</span>
            </div>
          </TabsContent>
          
          <TabsContent value="oscillators" className="m-0">
            <div className="space-y-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <h4 className="font-medium mb-3">RSI (14)</h4>
                <div className="relative pt-1">
                  <div className="grid grid-cols-3 text-xs text-muted-foreground mb-1">
                    <div className="text-left">Oversold</div>
                    <div className="text-center">Neutral</div>
                    <div className="text-right">Overbought</div>
                  </div>
                  <div className="h-4 flex rounded overflow-hidden">
                    <div className="bg-green-500 flex items-center justify-center text-xs text-white font-medium" style={{ width: '30%' }}>0-30</div>
                    <div className="bg-secondary flex-1 flex items-center justify-center text-xs font-medium" style={{ width: '40%' }}>30-70</div>
                    <div className="bg-red-500 flex items-center justify-center text-xs text-white font-medium" style={{ width: '30%' }}>70-100</div>
                  </div>
                  <div 
                    className="absolute w-2 h-4 bg-primary bottom-0 -mb-1 transform -translate-x-1/2 rounded"
                    style={{ left: `${indicators.indicators.rsi.current}%` }}
                  ></div>
                  <div className="mt-3 flex justify-between items-center">
                    <div>
                      <span className="text-sm font-semibold">Current: {indicators.indicators.rsi.current.toFixed(1)}</span>
                      <span className="text-xs ml-2 text-muted-foreground">
                        Previous: {indicators.indicators.rsi.previous.toFixed(1)}
                      </span>
                    </div>
                    <div>
                      {getSignalBadge('rsi', indicators.indicators.rsi.signal)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-muted/50 p-3 rounded-md">
                <h4 className="font-medium mb-3">MACD (12,26,9)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium mb-1">MACD Values</div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground">MACD Line:</span>
                        <span className={indicators.indicators.macd.value >= 0 ? "text-green-500" : "text-red-500"}>
                          {indicators.indicators.macd.value.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground">Signal Line:</span>
                        <span>{indicators.indicators.macd.signal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground">Histogram:</span>
                        <span className={indicators.indicators.macd.histogram >= 0 ? "text-green-500" : "text-red-500"}>
                          {indicators.indicators.macd.histogram.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium mb-1">Signal</div>
                    <div className="space-y-2">
                      <div className="flex items-center">
                        {getSignalBadge('macd', indicators.indicators.macd.trend)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {indicators.indicators.macd.trend === 'bullish' ? 
                          'MACD line is above signal line, indicating bullish momentum' : 
                          indicators.indicators.macd.trend === 'bearish' ?
                          'MACD line is below signal line, indicating bearish momentum' :
                          'MACD line is crossing the signal line, indicating potential trend change'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="moving-averages" className="m-0">
            <div className="space-y-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium">Simple Moving Averages</h4>
                  {getSignalBadge('movingAverages', indicators.indicators.movingAverages.signal)}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">SMA (20)</span>
                    <span className="font-medium">${indicators.indicators.movingAverages.sma20.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">SMA (50)</span>
                    <span className="font-medium">${indicators.indicators.movingAverages.sma50.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">SMA (200)</span>
                    <span className="font-medium">${indicators.indicators.movingAverages.sma200.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-muted/50 p-3 rounded-md">
                <h4 className="font-medium mb-3">Exponential Moving Averages</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">EMA (9)</span>
                    <span className="font-medium">${indicators.indicators.movingAverages.ema9.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">EMA (21)</span>
                    <span className="font-medium">${indicators.indicators.movingAverages.ema21.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-muted/50 p-3 rounded-md">
                <h4 className="font-medium mb-2">Volume Analysis</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Current Volume</span>
                    <span className="font-medium">{formatVolume(indicators.indicators.volume.current)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Average Volume</span>
                    <span className="font-medium">{formatVolume(indicators.indicators.volume.average)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Volume Ratio</span>
                    <div className="flex items-center">
                      <span className="font-medium mr-2">{indicators.indicators.volume.ratio.toFixed(2)}</span>
                      {getSignalBadge('volume', indicators.indicators.volume.trend)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </CardContent>
      </Tabs>
    </Card>
  );
} 