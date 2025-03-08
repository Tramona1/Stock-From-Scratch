# Intelligent Watchlist-Driven Data Scheduler

## Core Concept

The Stock Analytics Dashboard uses a smart data collection system that only fetches data that users actually care about. This document outlines the architecture of our watchlist-driven scheduler, which balances data freshness with API efficiency.

## Key Design Principles

1. **Data on Demand**: Only fetch data for stocks in user watchlists
2. **Just-in-Time Collection**: Trigger immediate data collection when users add new tickers
3. **Tiered Scheduling**: Different refresh rates for different data types
4. **API Efficiency**: Batch requests and respect rate limits
5. **Priority-Based Fetching**: More important/volatile data types fetch more frequently

## System Components

### 1. Watchlist Listener

A dedicated service that monitors changes to the `watchlists` table in Supabase:

```python
def monitor_watchlist_changes():
    # Set up Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Get the last processed timestamp
    last_processed = get_last_processed_timestamp()
    
    # Query for new watchlist entries
    result = supabase.table('watchlists') \
        .select('ticker, user_id, created_at') \
        .gt('created_at', last_processed) \
        .order('created_at') \
        .execute()
    
    # Process new tickers
    new_tickers = set()
    for item in result.data:
        ticker = item['ticker']
        new_tickers.add(ticker)
        
    # Trigger data collection for new tickers
    if new_tickers:
        trigger_immediate_data_collection(list(new_tickers))
    
    # Update the last processed timestamp
    set_last_processed_timestamp(datetime.now().isoformat())
```

This service runs every minute to detect new watchlist additions.

### 2. Ticker Registry

A persistent store that tracks which tickers need data collection:

```python
def update_ticker_registry(tickers, activation_reason="watchlist"):
    """
    Add tickers to the registry for scheduled collection
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    for ticker in tickers:
        # Check if ticker already exists
        result = supabase.table('ticker_registry') \
            .select('ticker') \
            .eq('ticker', ticker) \
            .execute()
            
        if not result.data:
            # Add new ticker to registry
            supabase.table('ticker_registry').insert({
                'ticker': ticker,
                'is_active': True,
                'first_added': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'activation_reason': activation_reason,
                'watchlist_count': 1
            }).execute()
        else:
            # Update existing ticker
            supabase.table('ticker_registry') \
                .update({
                    'is_active': True,
                    'last_updated': datetime.now().isoformat(),
                    'watchlist_count': supabase.rpc('increment_watchlist_count', { 'ticker_param': ticker }).execute()
                }) \
                .eq('ticker', ticker) \
                .execute()
```

### 3. Immediate Data Collection

When new tickers are added, an immediate data collection is triggered:

```python
def trigger_immediate_data_collection(tickers):
    """
    Trigger immediate data collection for new tickers
    """
    # Update the registry first
    update_ticker_registry(tickers, "new_watchlist_addition")
    
    # Run each data fetcher for these specific tickers
    run_fetcher_for_tickers("fetch_stock_info.py", tickers)
    run_fetcher_for_tickers("fetch_insider_trades.py", tickers)
    run_fetcher_for_tickers("fetch_analyst_ratings.py", tickers)
    run_fetcher_for_tickers("fetch_options_flow.py", tickers)
    
    # Log the operation
    logger.info(f"Triggered immediate data collection for tickers: {', '.join(tickers)}")
```

### 4. Scheduled Collection with Prioritization

The main scheduler that respects your refresh rates while focusing on watchlist tickers:

```python
def schedule_data_collection():
    """
    Set up the main scheduler with appropriate frequencies
    """
    # Stock Prices (every 5 minutes)
    schedule.every(5).minutes.do(lambda: run_fetcher_for_active_tickers("fetch_stock_prices.py"))
    
    # Options Flow (every 15 minutes)
    schedule.every(15).minutes.do(lambda: run_fetcher_for_active_tickers("fetch_options_flow.py"))
    
    # Dark Pool Data (hourly)
    schedule.every(1).hours.do(lambda: run_fetcher_for_active_tickers("fetch_dark_pool.py"))
    
    # Analyst Ratings (daily)
    schedule.every(1).days.at("08:00").do(lambda: run_fetcher_for_active_tickers("fetch_analyst_ratings.py"))
    
    # Insider Trading (daily)
    schedule.every(1).days.at("09:00").do(lambda: run_fetcher_for_active_tickers("fetch_insider_trades.py"))
    
    # Financial News (hourly)
    schedule.every(1).hours.do(lambda: run_fetcher_for_active_tickers("fetch_financial_news.py"))
    
    # Other data types according to your schedule...
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

### 5. Active Ticker Fetching

The helper function that only fetches data for active tickers:

```python
def run_fetcher_for_active_tickers(fetcher_script):
    """
    Run a fetcher script only for tickers in the active registry
    """
    # Get active tickers from the registry
    active_tickers = get_active_tickers_from_registry()
    
    if not active_tickers:
        logger.info(f"No active tickers to process for {fetcher_script}")
        return
        
    # Run the fetcher with these specific tickers
    run_fetcher_for_tickers(fetcher_script, active_tickers)
```

### 6. Watchlist Cleanup

A service that removes tickers from active collection when no users are watching them:

```python
def cleanup_inactive_tickers():
    """
    Deactivate tickers that are no longer in any user's watchlist
    """
    # Get current watchlist tickers
    current_watchlist_tickers = get_all_watchlist_tickers()
    
    # Get registry tickers
    registry_tickers = get_all_registry_tickers()
    
    # Find tickers in registry but not in any watchlist
    inactive_tickers = [t for t in registry_tickers if t not in current_watchlist_tickers]
    
    # Deactivate these tickers
    for ticker in inactive_tickers:
        deactivate_ticker(ticker)
        
    logger.info(f"Deactivated {len(inactive_tickers)} tickers no longer in any watchlist")
```

## Database Schema: Ticker Registry Table

Create a new table to track which tickers are actively being monitored:

```sql
CREATE TABLE IF NOT EXISTS public.ticker_registry (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT TRUE,
  first_added TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  watchlist_count INTEGER DEFAULT 1,
  activation_reason TEXT,
  last_collected JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE public.ticker_registry IS 'Tracks tickers for active data collection';
```

## Implementation Strategy

1. **Deploy in Phases**:
   - Phase 1: Implement watchlist listener and immediate data collection
   - Phase 2: Add scheduled collection with basic prioritization
   - Phase 3: Implement advanced prioritization and cleanup

2. **Integration with Existing Fetchers**:
   - Modify fetcher scripts to accept a specific list of tickers
   - Update APIs to filter by ticker where possible
   - Batch requests to minimize API calls

3. **Recovery and Resilience**:
   - Implement monitoring of the listener service
   - Add retry logic for failed immediate collections
   - Create a recovery process for missed schedules

## Optimization Techniques

### 1. Batching API Requests

Group tickers into batches to minimize API calls:

```python
def batch_api_requests(tickers, batch_size=10):
    """Process tickers in batches to minimize API calls"""
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        yield batch
```

### 2. Tiered Storage Strategy

Implement a data retention policy:

- **Hot Tier**: Active watchlist tickers with full data collection
- **Warm Tier**: Recently inactive tickers with reduced collection frequency
- **Cold Tier**: Long-inactive tickers with minimal or no collection

### 3. Adaptive Scheduling

Adjust collection frequency based on market hours and volatility:

```python
def get_collection_frequency(data_type, ticker=None):
    """Determine collection frequency based on multiple factors"""
    base_frequency = CONFIG[data_type]['base_frequency']
    
    # Adjust for market hours
    if not is_market_open():
        return base_frequency * 2  # Collect half as often when market closed
        
    # Adjust for ticker-specific volatility
    if ticker and is_high_volatility(ticker):
        return base_frequency / 2  # Collect twice as often for volatile tickers
        
    return base_frequency
```

## Best Practices for API Usage

1. **Rate Limit Tracking**: Maintain counters for each API to avoid exceeding limits
2. **Exponential Backoff**: When rate limited, increase wait time between retries
3. **Priority Queueing**: Implement a queue system for immediate collection requests
4. **Caching**: Cache API responses to avoid redundant fetches

## Monitoring and Metrics

Track key metrics to evaluate and optimize scheduler performance:

- **Collection Efficiency**: Ratio of useful data collected to total API calls
- **Data Freshness**: Average age of data by type
- **API Usage**: Percentage of rate limits consumed
- **Response Time**: How quickly new watchlist additions are populated with data

## Conclusion

This watchlist-driven scheduler ensures that:

1. Users get data as soon as they add stocks to their watchlist
2. API resources are focused only on stocks users actually care about
3. Different data types update at appropriate frequencies
4. System resources are used efficiently

By implementing this approach, you'll maximize the value of your API calls while providing users with the most relevant and fresh data for their investment decisions. 