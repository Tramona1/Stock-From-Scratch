# Data Pipeline Architecture

## Overview

The Stock Analytics Dashboard data pipeline is responsible for fetching financial data from various external APIs, processing it, and storing it in the Supabase database. This document explains how data flows through the system and how it's kept up to date.

## Data Pipeline Components

### 1. Python Data Fetchers

The core of our data collection system consists of specialized Python fetcher modules:

- `fetch_insider_trades.py`: Retrieves insider trading activity
- `fetch_analyst_ratings.py`: Collects analyst ratings and price targets
- `fetch_options_flow.py`: Gathers options activity data
- `fetch_for_watchlist.py`: Optimized module that only fetches data for stocks in user watchlists
- `fetch_technical_indicators.py`: Retrieves technical indicators like MACD and RSI
- `fetch_forex_info.py`: Collects forex exchange rate data (e.g., EUR:USD)
- `fetch_commodity_info.py`: Gathers commodity price data (e.g., WTI, BRENT, COPPER)
- `fetch_crypto_info.py`: Retrieves cryptocurrency price and market data
- `fetch_market_news.py`: Collects market news and sentiment data
- Other specialized fetchers for different data types

Each fetcher follows a similar pattern:

```python
class DataTypeFetcher:
    def __init__(self):
        # Setup connections and configuration
        
    def fetch(self, days=30, limit=500, symbols=None):
        # Fetch data from the external API
        
    def process(self, raw_data):
        # Process and normalize raw data
        
    def store(self, processed_data):
        # Store data in Supabase
        
    def run(self, days=30, limit=500, symbols=None):
        # Orchestrate the full fetch-process-store pipeline
        
    def fetch_for_watchlist(self, watchlist_symbols, days=30):
        # Optimization for watchlist-based fetching
```

### 2. Scheduler System

The scheduler (`scheduler.py`) manages when and how often data is fetched:

```python
# Running on a schedule
def run_continuously(custom_intervals=None):
    schedule.every(12).hours.do(lambda: run_fetcher("fetch_insider_trades.py"))
    schedule.every(6).hours.do(lambda: run_fetcher("fetch_analyst_ratings.py"))
    schedule.every(1).hours.do(lambda: run_fetcher("fetch_options_flow.py"))
    schedule.every(4).hours.do(lambda: run_fetcher("fetch_technical_indicators.py"))
    schedule.every(6).hours.do(lambda: run_fetcher("fetch_forex_info.py"))
    schedule.every(12).hours.do(lambda: run_fetcher("fetch_commodity_info.py"))
    # Other scheduled jobs...
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for pending jobs
```

### 3. Watchlist Integration

The system prioritizes data relevant to users:

1. `get_all_watchlist_symbols()` retrieves all unique tickers from user watchlists
2. Fetchers use these symbols to prioritize which data to collect
3. This optimization ensures we focus on data users actually care about

## Data Update Cycle

### Scheduling Logic

Different data types are updated at different frequencies based on:

1. **Data volatility**: How quickly the data changes
2. **API rate limits**: Constraints imposed by data providers
3. **User expectations**: How fresh users expect certain data to be

The default update schedule is:

| Data Type | Update Frequency | Rationale |
|-----------|------------------|-----------|
| Insider Trades | Every 12 hours | Reported with delay, changes infrequently |
| Analyst Ratings | Every 6 hours | Time-sensitive but not real-time |
| Options Flow | Every 1 hour | More dynamic, users expect fresher data |
| Market Indicators | Every 30 minutes | Highly dynamic data |
| Technical Indicators | Every 4 hours | Calculated values, moderate volatility |
| Forex Rates | Every 6 hours | Moderate volatility, API constraints |
| Commodity Prices | Every 12 hours | Changes less frequently than forex |
| Cryptocurrency | Every 2 hours | Volatile but constrained by API limits |

### Incremental Updates

To optimize performance and respect API limits:

1. Fetchers typically only request data from the past X days (configurable)
2. The system uses the most recent data timestamp to fetch only newer data
3. This incremental approach minimizes redundant API calls

Example from `fetch_insider_trades.py`:

```python
def fetch(self, days=7, limit=200, symbols=None, min_value=None):
    # Get most recent trade date from database to avoid fetching old data
    last_trade_date = self.get_last_trade_date()
    
    # Only fetch newer data from the API
    params = {
        "after_date": last_trade_date.isoformat() if last_trade_date else None,
        "limit": limit
    }
    
    # Add request filters
    if symbols:
        params["symbols"] = ",".join(symbols)
    if min_value:
        params["min_value"] = min_value
        
    # Make the API request
    response = requests.get(API_ENDPOINT, params=params, headers=self.headers)
    # Process and store...
```

## Supabase Integration

### Writing to Supabase

Data fetchers use the Supabase Python client to write data:

```python
def store(self, processed_trades):
    # Connect to Supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    # Store data with upsert (insert if not exists, update if exists)
    for trade in processed_trades:
        # Check if record exists
        response = supabase.table("insider_trades").upsert(trade).execute()
```

### Data Consistency Mechanisms

To maintain data integrity:

1. **Upsert operations**: Prevent duplicate records while allowing updates
2. **Transaction batching**: Group related operations to ensure atomicity
3. **Unique constraints**: Database-level protection against duplicates
4. **Indexing**: Optimizes query performance for frequently accessed data

### Timezone Handling

All data is stored with timezone-aware timestamps to ensure proper temporal comparisons:

1. Fetchers convert all timestamps to UTC before storage
2. Date comparisons use timezone-aware datetime objects
3. This approach prevents issues with daylight saving time and regional differences

## Error Handling and Resilience

The pipeline includes robust error handling:

1. **Retry logic**: Automatically retry failed API requests with exponential backoff
2. **Error notifications**: Send alerts on critical failures
3. **Logging**: Comprehensive logging for debugging and auditing

```python
def send_error_notification(fetcher_name, error_message):
    # Log the error
    logger.error(f"Error in {fetcher_name}: {error_message}")
    
    # Send email notification if configured
    if SENDGRID_API_KEY and ADMIN_EMAIL:
        try:
            message = Mail(
                from_email="alerts@stockanalytics.com",
                to_emails=ADMIN_EMAIL,
                subject=f"Error in data fetcher: {fetcher_name}",
                plain_text_content=f"Error details: {error_message}"
            )
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
```

## Monitoring and Health Checks

A dedicated health API (`health_api.py`) monitors the data pipeline:

1. **Pipeline status**: Checks if the scheduler is running
2. **Data freshness**: Verifies when tables were last updated
3. **API endpoints**: Provides monitoring for external systems

```python
@app.route('/health/tables')
def table_health():
    """Check the health of data tables"""
    try:
        results = {}
        tables = [
            "insider_trades", "analyst_ratings", "options_flow", 
            "market_indicators", "stock_info", "technical_indicators",
            "forex_info", "commodity_info"
        ]
        
        for table in tables:
            last_updated = get_last_updated_time(table)
            status = "healthy"
            
            # Mark as stale if data is too old (varies by table)
            if last_updated:
                age_hours = (datetime.now() - last_updated).total_seconds() / 3600
                threshold = TABLE_FRESHNESS_THRESHOLDS.get(table, 48)
                
                if age_hours > threshold:
                    status = "stale"
            else:
                status = "empty"
                
            results[table] = {
                "status": status,
                "last_updated": last_updated.isoformat() if last_updated else None,
                "record_count": get_record_count(table)
            }
            
        return jsonify({
            "status": "healthy" if all(r["status"] == "healthy" for r in results.values()) else "warning",
            "tables": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

## Manual Data Update Triggers

Besides scheduled updates, data can be manually updated:

1. **CLI commands**: Run individual fetchers on demand
2. **One-time run**: Update all data types at once

```bash
# Update forex info only
python python/fetch_forex_info.py --pairs EUR:USD,JPY:USD

# Update commodity info only
python python/fetch_commodity_info.py --commodities WTI,BRENT,NATURAL_GAS

# Update technical indicators for a specific stock
python python/fetch_technical_indicators.py --symbols AAPL,MSFT --interval daily
```

## Deployment and Production Considerations

In production, the data pipeline runs as a containerized service:

1. **Docker container**: Isolates the environment and dependencies
2. **Volume persistence**: Maintains state between restarts 
3. **Resource limitations**: Configured with appropriate CPU/memory limits
4. **Health monitoring**: Integrated with container orchestration

The `docker-compose.yml` configuration manages this service:

```yaml
# Python Data Fetcher Service
data-fetcher:
  build:
    context: .
    dockerfile: Dockerfile.python
  environment:
    SUPABASE_URL: ${SUPABASE_URL}
    SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
    API_KEY_UNUSUAL_WHALES: ${API_KEY_UNUSUAL_WHALES}
    API_KEY_ALPHA_VANTAGE: ${API_KEY_ALPHA_VANTAGE}
    SENDGRID_API_KEY: ${SENDGRID_API_KEY}
    ADMIN_EMAIL: ${ADMIN_EMAIL}
  volumes:
    - data-fetcher-logs:/app/logs
  restart: always
  networks:
    - stock-analytics-network
```

## Configuration and Customization

The data pipeline is highly configurable through:

1. **Environment variables**: Control connections and API keys
2. **Configuration files**: Set fetching schedules and thresholds
3. **Command-line arguments**: Override default behaviors

## Conclusion

This data pipeline architecture ensures that your Supabase database is consistently populated with fresh, relevant financial data. By optimizing for watchlist-based fetching and using intelligent scheduling, the system balances data freshness with API rate limits and resource efficiency. 

Our implementation of technical indicators, forex, and commodity fetchers has further enhanced the data pipeline's capabilities, providing users with a comprehensive set of financial data to inform their investment decisions. 