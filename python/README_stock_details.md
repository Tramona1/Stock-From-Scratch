# Stock Details Fetcher

This script fetches detailed stock information from the Unusual Whales API and stores it in the Supabase database.

## Features

- Fetches comprehensive stock details from Unusual Whales API
- Stores data in a well-structured Supabase table with proper indexing
- Includes company information, sector, market cap, volume, dividend status, etc.
- Updates data weekly by default (configurable)
- Supports watchlist filtering and custom ticker lists
- Implements robust error handling and retry logic

## Database Schema

The script uses the `stock_details` table with the following schema:

```sql
CREATE TABLE stock_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker TEXT NOT NULL UNIQUE,
    company_name TEXT,
    short_name TEXT,
    sector TEXT,
    market_cap NUMERIC(20, 2),
    market_cap_size TEXT,
    avg_volume NUMERIC(20, 2),
    description TEXT,
    logo_url TEXT,
    issue_type TEXT,
    has_dividend BOOLEAN DEFAULT FALSE,
    has_earnings_history BOOLEAN DEFAULT FALSE,
    has_investment_arm BOOLEAN DEFAULT FALSE,
    has_options BOOLEAN DEFAULT FALSE,
    next_earnings_date DATE,
    earnings_announce_time TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

The full schema is available in `python/extra/stock_details_schema.sql`.

## Setup

1. Make sure your `.env` file contains the following variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   API_KEY_UNUSUAL_WHALES=your_unusual_whales_api_key
   ```

2. Create the database table using the SQL in `python/extra/stock_details_schema.sql`

3. Install required Python packages:
   ```
   pip install httpx python-dotenv
   ```

## Usage

### Basic Usage

Run the script without arguments to fetch details for default tickers or your watchlist:

```
python fetch_stock_details.py
```

### Specify Tickers

Fetch details for specific tickers:

```
python fetch_stock_details.py --tickers AAPL,MSFT,GOOG
```

### Watchlist Only

Only process tickers that are in your watchlist:

```
python fetch_stock_details.py --watchlist-only
```

## Comparison with Other Scripts

This script provides more detailed stock information compared to:

1. **fetch_stock_info.py** - The original Unusual Whales stock info fetcher that provides basic company data but doesn't include all details like investment arm status and issue type.

2. **fetch_stock_info_alpha.py** - The Alpha Vantage-based script that focuses on pricing data but lacks comprehensive company information.

## Data Update Frequency

The script is configured to update data weekly (every 7 days). This can be adjusted by modifying the `needs_update` method in the `StockDetailsFetcher` class.

## Error Handling

The script includes robust error handling with exponential backoff for API retries. It will attempt to retry failed requests up to 3 times (configurable via the `MAX_RETRIES` constant).

## Logging

All actions are logged to both console and `logs/stock_details_fetcher.log` for troubleshooting.

## Return Value

The script returns a JSON object with the following fields:
- `status`: "success", "partial_success", or "failure"
- `tickers_processed`: Number of tickers processed
- `successful`: Number of tickers successfully updated
- `failed`: Number of tickers that failed to update 