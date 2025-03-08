# Stock From Scratch: Scripts Documentation

This document provides a comprehensive overview of all data fetching scripts in the system, organized by the type of data they collect and their scheduled execution frequency.

## Scripts Included in Scheduler

The scheduler systematically runs the following scripts at their designated intervals, respecting API rate limits and market hours.

### 5-Minute Interval (High Frequency Data)

| Script | API Used | Data Collected | Market Hours Only | Priority |
|--------|----------|----------------|-------------------|----------|
| `fetch_stock_info_alpha.py` | Alpha Vantage | Current stock prices, daily highs/lows, 52-week ranges, volume | Yes | 1 (Highest) |
| `fetch_technical_indicators.py` | Alpha Vantage | Technical indicators (RSI, MACD, Moving Averages, etc.) | Yes | 2 |
| `fetch_crypto_info.py` | Alpha Vantage | Cryptocurrency prices, volume, market cap | No (24/7) | 1 (Highest) |

### 15-Minute Interval (Medium Frequency Data)

| Script | API Used | Data Collected | Market Hours Only | Priority |
|--------|----------|----------------|-------------------|----------|
| `fetch_options_flow.py` | Unusual Whales | Options flow data, including premium, sentiment, and volume | Yes | 1 (Highest) |
| `fetch_options_flow_alpha.py` | Alpha Vantage | Alternative options data from Alpha Vantage | Yes | 1 (Highest) |
| `fetch_forex_info.py` | Alpha Vantage | Foreign exchange rates and currency pair data | No | 2 |
| `fetch_commodity_info.py` | Alpha Vantage | Commodity prices (gold, oil, etc.) | No | 2 |

### 60-Minute Interval (Hourly Data)

| Script | API Used | Data Collected | Market Hours Only | Priority |
|--------|----------|----------------|-------------------|----------|
| `fetch_dark_pool_data.py` | Unusual Whales | Dark pool trading activity and off-exchange volume | No | 2 |
| `fetch_market_news.py` | Other (Web Scraping) | Financial news, headlines, and market updates | No | 3 |

### Daily Interval (24-Hour Data)

| Script | API Used | Data Collected | Market Hours Only | Priority |
|--------|----------|----------------|-------------------|----------|
| `fetch_analyst_ratings.py` | Unusual Whales | Stock analyst ratings, price targets, and recommendations | No | 3 |
| `fetch_insider_trades.py` | Unusual Whales | Company insider transactions (simplified version) | No | 3 |
| `insider_trades_fetcher.py` | Unusual Whales | Comprehensive insider trading data with analysis | No | 3 |
| `economic_indicators_fetcher.py` | Other (Web Scraping) | Economic indicators like GDP, unemployment, CPI | No | 4 |
| `fetch_economic_reports.py` | Other (Web Scraping) | Economic report calendar and releases | No | 4 |
| `fetch_fda_calendar.py` | Other (Web Scraping) | FDA decisions and pharmaceutical approval dates | No | 4 |
| `fetch_political_trades.py` | Unusual Whales | Congressional trading activity and political trades | No | 4 |

### Weekly Interval (7-Day Data)

| Script | API Used | Data Collected | Market Hours Only | Priority |
|--------|----------|----------------|-------------------|----------|
| `hedge_fund_fetcher.py` | Unusual Whales | Institutional holdings, 13F filings, hedge fund positions | No | 5 (Lowest) |

### Special Schedule

| Script | API Used | Data Collected | Schedule | Priority |
|--------|----------|----------------|----------|----------|
| `fetch_stock_info.py` | Unusual Whales | Company metadata, sectors, descriptions, logos | Mondays & Thursdays at 6:00 AM | 5 (Lowest) |
| `fetch_stock_details.py` | Unusual Whales | Enhanced company metadata including dividend status, issue type, etc. | Mondays & Thursdays at 6:00 AM | 5 (Lowest) |

## Additional Scripts (Not in Regular Scheduler)

These scripts are not part of the regular scheduler but serve specific purposes:

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `run_scheduler.sh` | Shell script to start/stop/monitor the scheduler as a background process |
| `scheduler.py` | Main scheduling system that manages all data fetcher execution |
| `setup_stock_details_db.py` | One-time script to set up the database tables for stock details |
| `health_api.py` | API health monitoring script |

### Alternative/Legacy Scripts

| Script | Purpose |
|--------|---------|
| `run_all_fetchers.py` | Legacy script to run all fetchers in sequence (replaced by scheduler) |
| `run_pipeline.py` | Alternative pipeline system for running data fetchers |
| `watchlist_scheduler.py` | Alternative watchlist-focused scheduler (specialized for watchlist tickers) |
| `fetch_for_watchlist.py` | Script to fetch data specifically for watchlist tickers |

## API Usage Distribution

The scripts are distributed across APIs to balance rate limits:

### Alpha Vantage API (75 requests/minute)
- `fetch_stock_info_alpha.py`
- `fetch_technical_indicators.py`
- `fetch_crypto_info.py`
- `fetch_forex_info.py`
- `fetch_commodity_info.py`
- `fetch_options_flow_alpha.py`

### Unusual Whales API (120 requests/minute)
- `fetch_stock_info.py`
- `fetch_stock_details.py`
- `fetch_options_flow.py`
- `fetch_dark_pool_data.py`
- `fetch_insider_trades.py`
- `insider_trades_fetcher.py`
- `fetch_political_trades.py`
- `fetch_analyst_ratings.py`
- `hedge_fund_fetcher.py`

### Other Sources (No API Rate Limits)
- `fetch_market_news.py`
- `fetch_economic_reports.py`
- `economic_indicators_fetcher.py`
- `fetch_fda_calendar.py`

## Data Collected Details

### Market Data
- **Stock Prices**: Current prices, daily highs/lows, 52-week ranges, market cap, volume (Alpha Vantage)
- **Technical Indicators**: RSI, MACD, moving averages, support/resistance levels (Alpha Vantage)
- **Options Data**: Option chains, premiums, volume, open interest, unusual activity (Unusual Whales & Alpha Vantage)
- **Crypto Prices**: Cryptocurrency prices, volume, market cap (Alpha Vantage)
- **Forex Data**: Currency exchange rates, historical trends (Alpha Vantage)
- **Commodity Prices**: Prices for gold, silver, oil, etc. (Alpha Vantage)
- **Dark Pool Activity**: Off-exchange trading volume and patterns (Unusual Whales)

### Fundamental Data
- **Company Information**: Sector, descriptions, logos, dividend status (Unusual Whales)
- **Analyst Ratings**: Buy/Sell recommendations, price targets (Unusual Whales)
- **Insider Trading**: Executive and board member stock transactions (Unusual Whales)
- **Institutional Holdings**: 13F filings, hedge fund positions (Unusual Whales)
- **Political Trading**: Congressional trading activity (Unusual Whales)

### Macro/News Data
- **Market News**: Financial headlines and market updates (Web Scraping)
- **Economic Indicators**: GDP, unemployment, inflation, etc. (Web Scraping)
- **Economic Calendars**: Upcoming economic releases and events (Web Scraping)
- **FDA Calendars**: Pharmaceutical approval dates and decisions (Web Scraping)

## Conclusion

The scheduler ensures all these scripts run at appropriate intervals, prioritizing critical real-time data during market hours while collecting less time-sensitive data at lower frequencies. The system respects API rate limits and ensures all data types are collected regularly without sacrificing the timeliness of critical market data. 