# Real Data Migration Plan: Watchlist-Driven Stock Data

## Overview

This document outlines the complete migration plan for transitioning from mock data to real stock data throughout the application. The strategy centers on a watchlist-driven approach where user watchlists determine which stocks receive priority for real-time data updates.

## Current State Assessment

Based on our code review and documentation analysis, we currently have:

1. **Frontend Watchlist Implementation**:
   - Functional `WatchlistContext` provider with add/remove/refresh capabilities
   - API routes for CRUD operations on watchlists
   - UI components for watchlist display and management

2. **Mock Data Generation**:
   - `generateMockPrice`, `generateMockChange`, and `generateMockVolume` functions in the watchlist API
   - Mock data is currently returned for all watchlist operations

3. **Data Fetchers**:
   - Python scripts for fetching stock data from external APIs (Unusual Whales, Alpha Vantage)
   - Scheduler system for running fetchers at specified intervals
   - Database tables for storing fetched data

4. **Database Structure**:
   - `watchlists` table for storing user-ticker relationships
   - `stock_info` table for basic stock data
   - `stock_details` table for comprehensive company information
   - Various other tables for specialized data types

## Dashboard Component Inventory

This section catalogs all frontend components on the user dashboard that will need to be integrated with real data.

### 1. Market Indicators (src/components/dashboard/MarketIndicators.tsx)
- **Current Functionality**: Displays overall market health indicators
- **Data Types Needed**:
  - Market indices (S&P 500, Nasdaq, Dow Jones)
  - Market momentum indicators
  - Sector performance
  - Trading volume metrics
  - Market volatility (VIX)
- **Data Sources**: 
  - `fetch_market_indicators.py`
  - `fetch_sector_performance.py`
  - Alpha Vantage API (for major indices)

### 2. Watchlist (src/components/dashboard/Watchlist.tsx)
- **Current Functionality**: Displays user's watchlisted stocks with basic price data
- **Data Types Needed**:
  - Current stock price
  - Price change ($ and %)
  - Trading volume
  - Company name
  - Last updated timestamp
- **Data Sources**:
  - `fetch_stock_info_alpha.py`
  - `fetch_stock_info.py`

### 3. Market Scanner (src/components/dashboard/MarketScanner.tsx)
- **Current Functionality**: Allows users to scan for stocks meeting specific criteria
- **Data Types Needed**:
  - Technical indicators (RSI, MACD)
  - Volume anomalies
  - Price movements
  - Candlestick patterns
  - Insider trading activity
- **Data Sources**:
  - `fetch_technical_indicators.py`
  - `fetch_insider_trades.py`
  - `fetch_options_flow.py`

### 4. AI Query Interface (src/components/dashboard/AiQueryInterface.tsx)
- **Current Functionality**: Allows natural language queries about stock data
- **Data Types Needed**:
  - All available stock data for context
  - Real-time question answering
  - Historical data for comparisons
  - News sentiment
- **Data Sources**:
  - Multiple API integration points
  - Processed data from all fetchers

### 5. Stock Detail View (src/components/stocks/StockDetail.tsx)
- **Current Functionality**: Shows comprehensive information about a selected stock
- **Data Types Needed**:
  - Company profile (sector, industry, description)
  - Key financials
  - Recent news
  - Technical indicators
  - Price chart data
  - Earnings information
- **Data Sources**:
  - `fetch_stock_details.py`
  - `fetch_company_financials.py`
  - `fetch_market_news.py`

### 6. Technical Analysis Panel (src/components/stocks/TechnicalAnalysis.tsx)
- **Current Functionality**: Displays technical analysis indicators for stocks
- **Data Types Needed**:
  - RSI, MACD, Bollinger Bands
  - Moving averages
  - Support/resistance levels
  - Volume analysis
  - Historical patterns
- **Data Sources**:
  - `fetch_technical_indicators.py`
  - Alpha Vantage API

### 7. Options Flow Panel (src/components/options/OptionsFlow.tsx)
- **Current Functionality**: Shows options activity for selected stocks
- **Data Types Needed**:
  - Options contracts
  - Premium data
  - Open interest
  - Implied volatility
  - Unusual options activity
- **Data Sources**:
  - `fetch_options_flow.py`
  - Unusual Whales API

### 8. News Feed (src/components/news/NewsFeed.tsx)
- **Current Functionality**: Displays financial news relevant to watchlisted stocks
- **Data Types Needed**:
  - News articles
  - Sentiment analysis
  - News categorization
  - Publication source
  - Relevance score
- **Data Sources**:
  - `fetch_market_news.py`
  - News API integration

### 9. Alerts Panel (src/components/alerts/AlertsPanel.tsx)
- **Current Functionality**: Shows and manages user alerts
- **Data Types Needed**:
  - Alert configurations
  - Triggered alerts
  - Alert history
  - Custom alert parameters
- **Data Sources**:
  - Supabase `alerts` table
  - Alert processing logic

### 10. Portfolio Performance (src/components/portfolio/PortfolioPerformance.tsx)
- **Current Functionality**: Shows performance metrics for user's watchlist
- **Data Types Needed**:
  - Aggregate performance
  - Sector allocation
  - Risk metrics
  - Historical returns
- **Data Sources**:
  - Derived from stock data
  - Portfolio analytics calculations

### Component-to-Data Mapping Matrix

| Component             | Basic Stock Info | Company Details | Technical Indicators | Options Data | News | Market Data | Alerts |
|-----------------------|-----------------|-----------------|----------------------|--------------|------|-------------|--------|
| Market Indicators     | ⬜              | ⬜              | ⬜                   | ⬜           | ⬜   | ✅          | ⬜     |
| Watchlist             | ✅              | ⬜              | ⬜                   | ⬜           | ⬜   | ⬜          | ⬜     |
| Market Scanner        | ✅              | ⬜              | ✅                   | ⬜           | ⬜   | ⬜          | ⬜     |
| AI Query Interface    | ✅              | ✅              | ✅                   | ✅           | ✅   | ✅          | ✅     |
| Stock Detail View     | ✅              | ✅              | ✅                   | ⬜           | ✅   | ⬜          | ⬜     |
| Technical Analysis    | ✅              | ⬜              | ✅                   | ⬜           | ⬜   | ⬜          | ⬜     |
| Options Flow Panel    | ✅              | ⬜              | ⬜                   | ✅           | ⬜   | ⬜          | ⬜     |
| News Feed             | ✅              | ⬜              | ⬜                   | ⬜           | ✅   | ⬜          | ⬜     |
| Alerts Panel          | ✅              | ⬜              | ✅                   | ✅           | ⬜   | ⬜          | ✅     |
| Portfolio Performance | ✅              | ✅              | ⬜                   | ⬜           | ⬜   | ✅          | ⬜     |

## Migration Strategy

The migration will follow a phased approach to gradually replace mock data with real data while ensuring a smooth user experience throughout the transition.

### Phase 1: Real-Time Stock Price Integration

#### 1. API Route Enhancement

Update `/api/watchlist` endpoints to fetch real stock data from Supabase instead of generating mock data:

```typescript
// src/app/api/watchlist/route.ts
export async function GET(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Ensure user exists in Supabase
    await createUserIfNotExists(userId);
    
    try {
      // Get watchlist tickers from Supabase
      const watchlistItems = await getUserWatchlist(userId);
      
      if (watchlistItems.length === 0) {
        return NextResponse.json({ success: true, watchlist: [] });
      }
      
      // Extract tickers for database query
      const tickers = watchlistItems.map(item => item.ticker);
      
      // Initialize Supabase client
      const supabase = createClient();
      
      // Fetch real stock data for watchlist tickers
      const { data: stockData, error: stockError } = await supabase
        .from('stock_info')
        .select('ticker, price, price_change_percent, volume, last_updated')
        .in('ticker', tickers);
      
      if (stockError) {
        console.error('Error fetching stock data:', stockError);
        throw new Error('Failed to fetch stock data');
      }
      
      // Map stock data to watchlist items
      const transformedWatchlist = watchlistItems.map(item => {
        // Find corresponding stock data
        const stock = stockData?.find(s => s.ticker === item.ticker);
        
        if (stock) {
          return {
            id: item.id,
            symbol: item.ticker,
            price: stock.price,
            change: stock.price_change_percent,
            volume: formatVolume(stock.volume),
            lastUpdated: stock.last_updated,
            watching: true
          };
        } else {
          // Fallback to mock data if real data isn't available yet
          console.warn(`No real data available for ${item.ticker}, using fallback`);
          return {
            id: item.id,
            symbol: item.ticker,
            price: generateMockPrice(item.ticker),
            change: generateMockChange(),
            volume: generateMockVolume(),
            lastUpdated: null,
            watching: true
          };
        }
      });
  
      return NextResponse.json({ 
        success: true, 
        watchlist: transformedWatchlist,
        dataSource: stockData?.length ? 'real' : 'mock'
      });
    } catch (fetchError) {
      console.error('Error fetching watchlist data:', fetchError);
      return NextResponse.json({ success: true, watchlist: [] });
    }
  } catch (error: any) {
    console.error('Error in watchlist API:', error);
    return NextResponse.json({ success: true, watchlist: [] });
  }
}

// Helper format functions
function formatVolume(volume: number): string {
  if (!volume) return '0';
  
  if (volume >= 1_000_000_000) {
    return `${(volume / 1_000_000_000).toFixed(1)}B`;
  } else if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(1)}M`;
  } else if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(1)}K`;
  }
  
  return volume.toString();
}
```

#### 2. Data Fetcher Optimization

Enhance `fetch_stock_info_alpha.py` to prioritize watchlist tickers:

```python
async def fetch_watchlist_tickers(self):
    """Fetch all tickers in any user's watchlist"""
    try:
        result = self.supabase.table("watchlists").select("ticker").execute()
        
        if result.data:
            # Extract unique tickers from the result
            tickers = set(item["ticker"] for item in result.data)
            logger.info(f"Found {len(tickers)} unique tickers in user watchlists")
            return list(tickers)
        else:
            logger.info("No watchlist tickers found")
            return []
    except Exception as e:
        logger.error(f"Error fetching watchlist tickers: {str(e)}")
        return []

async def run(self, tickers=None, watchlist_only=False):
    """Run the stock info fetcher with optional filtering"""
    try:
        start_time = time.time()
        processed_count = 0
        failed_count = 0
        
        # If no tickers specified, fetch from watchlist
        if not tickers:
            watchlist_tickers = await self.fetch_watchlist_tickers()
            
            if watchlist_tickers:
                tickers = watchlist_tickers
                logger.info(f"Using {len(tickers)} tickers from user watchlists")
            else:
                # Fall back to default tickers if no watchlist tickers
                tickers = DEFAULT_TICKERS
                logger.info(f"Using {len(tickers)} default tickers")
        
        # Process tickers with prioritization for watchlist items
        for ticker in tickers:
            try:
                needs_update = await self.needs_update(ticker)
                
                if needs_update:
                    logger.info(f"Processing ticker {ticker}")
                    success = await self.process_ticker(ticker)
                    
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                else:
                    logger.info(f"Skipping {ticker} - data is current")
            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {str(e)}")
                failed_count += 1
        
        elapsed_time = time.time() - start_time
        logger.info(f"Fetcher completed in {elapsed_time:.2f}s. Processed: {processed_count}, Failed: {failed_count}")
        
        return {
            "status": "success" if failed_count == 0 else "partial_success" if processed_count > 0 else "failure",
            "tickers_processed": len(tickers),
            "successful": processed_count,
            "failed": failed_count,
            "elapsed_time": elapsed_time
        }
    except Exception as e:
        logger.error(f"Error running stock info fetcher: {str(e)}")
        return {
            "status": "failure",
            "error": str(e)
        }
```

#### 3. Scheduler Updates

Modify the scheduler to prioritize watchlist-related data fetching:

```python
def get_watchlist_tickers() -> List[str]:
    """Get all unique tickers from all users' watchlists"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = supabase.table("watchlists").select("ticker").execute()
        
        if result.data:
            # Extract unique tickers
            tickers = set(item["ticker"] for item in result.data)
            return list(tickers)
        return []
    except Exception as e:
        logging.error(f"Error fetching watchlist tickers: {str(e)}")
        return []

def run_script(script_name: str) -> bool:
    """Run a script with watchlist prioritization if applicable"""
    try:
        # Check if this script should prioritize watchlist tickers
        watchlist_priority_scripts = [
            "fetch_stock_info_alpha.py",
            "fetch_technical_indicators.py",
            "fetch_options_flow.py",
        ]
        
        if script_name in watchlist_priority_scripts:
            # Get watchlist tickers
            tickers = get_watchlist_tickers()
            
            if tickers:
                # Run script with watchlist tickers
                extra_args = ["--tickers", ",".join(tickers)]
                return run_script_with_args(script_name, extra_args)
        
        # Default execution without watchlist prioritization
        return run_script_with_args(script_name, [])
    except Exception as e:
        logging.error(f"Error running script {script_name}: {str(e)}")
        return False
```

### Phase 2: Historical Data Integration

Implement historical data fallbacks for non-market hours:

```typescript
// src/lib/market.ts
export function isMarketOpen(): boolean {
  const now = new Date();
  const day = now.getDay();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  
  // Convert to ET (UTC-5 or UTC-4 during DST)
  const et = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const etHours = et.getHours();
  const etMinutes = et.getMinutes();
  
  // Market is closed on weekends
  if (day === 0 || day === 6) return false;
  
  // Market hours: 9:30 AM - 4:00 PM ET
  const marketOpen = etHours > 9 || (etHours === 9 && etMinutes >= 30);
  const marketClose = etHours < 16;
  
  return marketOpen && marketClose;
}

// src/app/api/stocks/[ticker]/route.ts
export async function GET(req: NextRequest, { params }: { params: { ticker: string } }) {
  try {
    const { ticker } = params;
    
    if (!ticker) {
      return NextResponse.json({ error: 'Ticker is required' }, { status: 400 });
    }
    
    const supabase = createClient();
    
    // First try to get the latest stock data
    const { data: stockData, error: stockError } = await supabase
      .from('stock_info')
      .select('*')
      .eq('ticker', ticker.toUpperCase())
      .single();
    
    if (stockError) {
      console.error(`Error fetching stock data for ${ticker}:`, stockError);
      return NextResponse.json({ error: 'Stock data not found' }, { status: 404 });
    }
    
    // Check if we need historical data
    const isMarketCurrentlyOpen = isMarketOpen();
    const lastUpdated = new Date(stockData.last_updated);
    const now = new Date();
    const dataAge = now.getTime() - lastUpdated.getTime();
    const dataAgeHours = dataAge / (1000 * 60 * 60);
    
    // If market is closed and data is older than 4 hours, get historical data
    if (!isMarketCurrentlyOpen && dataAgeHours > 4) {
      // Fetch historical data
      const { data: historicalData, error: historicalError } = await supabase
        .from('historical_prices')
        .select('*')
        .eq('ticker', ticker.toUpperCase())
        .order('date', { ascending: false })
        .limit(30);
      
      if (!historicalError && historicalData?.length) {
        return NextResponse.json({
          ...stockData,
          historical: historicalData,
          marketStatus: 'closed',
          dataSource: 'historical'
        });
      }
    }
    
    // Return real-time data
    return NextResponse.json({
      ...stockData,
      marketStatus: isMarketCurrentlyOpen ? 'open' : 'closed',
      dataSource: 'real-time'
    });
  } catch (error: any) {
    console.error('Error fetching stock data:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
```

### Phase 3: UI Enhancement for Data Source Transparency

Update watchlist UI to show data source and freshness:

```tsx
function StockListItem({ stock, onRemove }) {
  const isPositive = stock.change > 0;
  const isRealData = Boolean(stock.lastUpdated);
  const dataAge = isRealData 
    ? getTimeAgo(new Date(stock.lastUpdated))
    : null;
  
  return (
    <div className="flex items-center justify-between py-2 border-b">
      <div>
        <div className="font-medium">{stock.symbol}</div>
        <div className="text-sm text-muted-foreground">{stock.companyName || ''}</div>
      </div>
      
      <div className="text-right">
        <div className="font-medium">${stock.price.toFixed(2)}</div>
        <div className={isPositive ? "text-green-500" : "text-red-500"} className="flex items-center">
          {isPositive ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
          {Math.abs(stock.change).toFixed(2)}%
        </div>
        {dataAge && (
          <div className="text-xs text-muted-foreground mt-1">
            {dataAge}
          </div>
        )}
      </div>
      
      <Button variant="ghost" size="sm" onClick={onRemove}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Helper function to format time ago
function getTimeAgo(date) {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  
  return new Date(date).toLocaleDateString();
}
```

## Implementation Checklist

### Backend Changes

- [ ] **Data Fetcher Enhancements**
  - [ ] Update `fetch_stock_info_alpha.py` to prioritize watchlist tickers
  - [ ] Enhance `fetch_technical_indicators.py` for watchlist prioritization
  - [ ] Add retry logic and enhanced error handling to all fetchers
  - [ ] Implement historical data storage

- [ ] **Scheduler Updates**
  - [ ] Add watchlist ticker extraction function
  - [ ] Modify script execution to prioritize watchlist tickers
  - [ ] Adjust scheduling frequency for real-time data needs
  - [ ] Add special handling for market hours vs. after-hours

- [ ] **Database Indices**
  - [ ] Ensure proper indices on `ticker` columns for fast lookups
  - [ ] Add indices on `last_updated` for quick recency checks
  - [ ] Create composite indices for efficient filtering

### API Routes

- [ ] **Watchlist API Updates**
  - [ ] Modify `GET /api/watchlist` to use real data
  - [ ] Update `POST /api/watchlist` to trigger immediate data fetch
  - [ ] Enhance `DELETE /api/watchlist` to maintain data consistency

- [ ] **Stock Data API Creation**
  - [ ] Create `GET /api/stocks/[ticker]` for individual stock data
  - [ ] Implement `GET /api/stocks/historical/[ticker]` for price history
  - [ ] Add `GET /api/market/status` for market open/close information

- [ ] **Technical Indicators API**
  - [ ] Implement `GET /api/indicators/[ticker]` for technical analysis data
  - [ ] Create charting data endpoint for visualizations

### Frontend Updates

- [ ] **Context Provider Enhancements**
  - [ ] Update `WatchlistContext` to handle real data attributes
  - [ ] Add data freshness indicators and auto-refresh logic
  - [ ] Implement proper loading states for data transitions

- [ ] **UI Component Updates**
  - [ ] Enhance `Watchlist` component to display real data
  - [ ] Create fallback states for missing data
  - [ ] Add data age indicators and refresh buttons
  - [ ] Implement proper error handling and user feedback

- [ ] **Dashboard Integration**
  - [ ] Update stock charts to use real data
  - [ ] Enhance market indicators with real-time information
  - [ ] Modify AI query interface to reference real data

## Gradual Migration Approach

To ensure a smooth transition, we'll follow these principles:

1. **Progressive Enhancement**: Start with basic price data, then add more complex data types
2. **Graceful Fallbacks**: Always have fallback to mock data when real data is unavailable
3. **User Communication**: Clearly indicate data sources and freshness to users
4. **Monitoring**: Implement logging to track migration progress and data quality
5. **Parallel Systems**: Run both mock and real data systems initially, comparing results

## Success Metrics

We'll measure the success of this migration using:

1. **Data Completeness**: Percentage of watchlist stocks with real data
2. **Data Freshness**: Average age of displayed stock data during market hours
3. **System Performance**: Response times for watchlist and stock detail pages
4. **Error Rates**: Number of failed data fetches or API errors
5. **User Engagement**: Changes in user interaction with stock data elements

## Rollback Plan

If issues arise during migration, we can roll back by:

1. Reverting API routes to use mock data generators
2. Disabling watchlist-based fetcher prioritization
3. Restoring previous UI components that don't expect real data attributes

## Timeline

| Phase | Duration | Components | Success Criteria |
|-------|----------|------------|------------------|
| 1: Basic Price Data | 1 week | Stock price, change, volume | 90% of watchlist stocks show real data during market hours |
| 2: Historical Data | 1 week | Price history, charts | Historical data available for all stocks in watchlist |
| 3: Company Details | 1 week | Company info, sectors, market cap | Complete company profiles available for all watchlist stocks |
| 4: Technical Indicators | 1 week | RSI, MACD, moving averages | Technical indicators available for analysis |
| 5: Advanced Data | 2 weeks | Options flow, insider trades | Complete data ecosystem with all planned data types |

## Conclusion

This migration plan provides a structured approach to transitioning from mock data to real stock data throughout the application. By focusing first on watchlist stocks and implementing graceful fallbacks, we'll ensure a smooth experience for users while incrementally enhancing the system with real financial data. 