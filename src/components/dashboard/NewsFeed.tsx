"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { AlertTriangle, Calendar, Clock, ExternalLink, Filter, Loader2, MessageSquare, RefreshCw, Share2, Newspaper } from "lucide-react"

// Define the news article type
interface NewsArticle {
  id: string
  title: string
  summary: string
  url: string
  source: string
  publishedAt: string
  sentiment: 'positive' | 'negative' | 'neutral'
  sentimentScore?: number
  relatedTickers?: string[]
  imageUrl?: string
  category?: string
  authors?: string[]
}

// Mock data for initial display
const mockNews: NewsArticle[] = [
  {
    id: '1',
    title: 'Fed signals potential rate cut later this year as inflation eases',
    summary: 'Federal Reserve officials indicated they may begin cutting interest rates in the coming months if inflation continues to cool, according to meeting minutes released Wednesday.',
    url: 'https://example.com/fed-news',
    source: 'Financial Times',
    publishedAt: '2023-08-16T14:30:00Z',
    sentiment: 'positive',
    sentimentScore: 0.78,
    relatedTickers: ['SPY', 'QQQ', 'TLT'],
    category: 'Economy'
  },
  {
    id: '2',
    title: 'Apple unveils new AI features for iPhone at developer conference',
    summary: 'Apple announced a range of new AI capabilities for its iOS platform, signaling the company\'s push into generative artificial intelligence.',
    url: 'https://example.com/apple-ai',
    source: 'TechCrunch',
    publishedAt: '2023-08-15T18:45:00Z',
    sentiment: 'positive',
    sentimentScore: 0.85,
    relatedTickers: ['AAPL', 'MSFT', 'NVDA'],
    category: 'Technology'
  },
  {
    id: '3',
    title: 'Oil prices fall as demand concerns outweigh supply disruptions',
    summary: 'Crude oil prices declined sharply on Wednesday as worries about global economic growth and fuel demand offset concerns about supply disruptions in the Middle East.',
    url: 'https://example.com/oil-prices',
    source: 'Reuters',
    publishedAt: '2023-08-16T10:15:00Z',
    sentiment: 'negative',
    sentimentScore: 0.32,
    relatedTickers: ['XOM', 'CVX', 'USO'],
    category: 'Commodities'
  },
  {
    id: '4',
    title: 'Retail sales beat expectations in July, showing resilient consumer spending',
    summary: 'U.S. retail sales rose more than expected in July, suggesting that consumer spending remains strong despite inflation pressures.',
    url: 'https://example.com/retail-sales',
    source: 'CNBC',
    publishedAt: '2023-08-15T13:20:00Z',
    sentiment: 'positive',
    sentimentScore: 0.67,
    relatedTickers: ['WMT', 'TGT', 'AMZN'],
    category: 'Economy'
  }
];

// Format date to relative time (e.g., "2 hours ago")
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  
  // Convert to seconds, minutes, hours, days
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffDays > 0) {
    return diffDays === 1 ? '1 day ago' : `${diffDays} days ago`;
  } else if (diffHours > 0) {
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
  } else if (diffMins > 0) {
    return diffMins === 1 ? '1 minute ago' : `${diffMins} minutes ago`;
  } else {
    return 'Just now';
  }
}

export function NewsFeed() {
  const [news, setNews] = useState<NewsArticle[]>(mockNews);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [error, setError] = useState<string | null>(null);
  
  // Refresh news data
  const refreshNews = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // This will be replaced with actual API call later
      // const response = await fetch('/api/news');
      // const data = await response.json();
      // setNews(data.news);
      
      // For now, just simulate an API call
      setTimeout(() => {
        setNews(mockNews);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Failed to load news');
      setIsLoading(false);
    }
  };
  
  // Filter news by category
  const filteredNews = activeTab === 'all' 
    ? news 
    : news.filter(article => article.category?.toLowerCase() === activeTab);
  
  // Get unique categories for tabs
  const categories = ['all', ...Array.from(new Set(news.map(article => article.category?.toLowerCase() || 'other')))];
  
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center">
          <Newspaper className="h-5 w-5 mr-2" />
          Market News
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshNews}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      
      <Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab}>
        <div className="px-4">
          <TabsList className="mb-2 w-full justify-start overflow-x-auto py-1">
            {categories.map(category => (
              <TabsTrigger key={category} value={category} className="capitalize">
                {category}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
        
        <CardContent className="p-4 pt-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-6 flex flex-col items-center justify-center">
              <AlertTriangle className="h-10 w-10 text-muted-foreground mb-2" />
              <p className="text-muted-foreground font-medium">{error}</p>
              <Button variant="outline" size="sm" onClick={refreshNews} className="mt-4">
                Try Again
              </Button>
            </div>
          ) : filteredNews.length === 0 ? (
            <div className="text-center py-6 flex flex-col items-center justify-center">
              <MessageSquare className="h-10 w-10 text-muted-foreground mb-2" />
              <p className="text-muted-foreground font-medium">No news available</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredNews.map((article) => (
                <div key={article.id} className="border-b pb-4 last:border-0 last:pb-0">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-medium line-clamp-2">{article.title}</h3>
                    <Badge 
                      variant={article.sentiment === 'positive' ? 'outline' : 
                             article.sentiment === 'negative' ? 'destructive' : 'secondary'}
                      className="ml-2 whitespace-nowrap"
                    >
                      {article.sentiment}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                    {article.summary}
                  </p>
                  
                  <div className="flex flex-wrap items-center justify-between text-xs text-muted-foreground mt-2">
                    <div className="flex items-center">
                      <span className="font-medium mr-3">{article.source}</span>
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatRelativeTime(article.publishedAt)}
                      </span>
                    </div>
                    
                    <div className="flex space-x-2 mt-1 sm:mt-0">
                      {article.relatedTickers && article.relatedTickers.length > 0 && (
                        <span className="flex items-center text-xs">
                          <span className="mr-1">Tickers:</span>
                          {article.relatedTickers.map((ticker, i) => (
                            <Badge key={ticker} variant="secondary" className="text-[10px] px-1 mr-1 h-4">
                              {ticker}
                            </Badge>
                          ))}
                        </span>
                      )}
                      
                      <a 
                        href={article.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-primary hover:underline flex items-center"
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        Read
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Tabs>
    </Card>
  );
} 