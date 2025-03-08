# Frontend Components Inventory

This document provides a comprehensive list of all frontend components in the application that will need to be integrated with real data as part of our migration away from mock data.

## Dashboard Core Components

1. **MarketIndicators** (`src/components/dashboard/MarketIndicators.tsx`)
   - Displays market indices, trading day status, and market sentiment
   - Needs real market index data, volume metrics, and volatility indicators

2. **Watchlist** (`src/components/dashboard/Watchlist.tsx`)
   - Shows user's selected stocks with price information
   - Needs real-time price data, company names, price change percentages, and volume

3. **MarketScanner** (`src/components/dashboard/MarketScanner.tsx`)
   - Allows filtering stocks based on technical and fundamental criteria
   - Needs technical indicators, volume alerts, and price movement data

4. **AiQueryInterface** (`src/components/dashboard/AiQueryInterface.tsx`)
   - Natural language interface for querying stock information
   - Needs access to all data sources for contextual answers

5. **TickerInput** (`src/components/dashboard/TickerInput.tsx`)
   - Input component for entering stock tickers
   - Needs symbol validation against real data

## Chart Components

6. **StockChart** (`src/components/dashboard/charts/StockChart.tsx`)
   - Displays price charts for individual stocks
   - Needs historical price data, volume data, and technical overlays

7. **MarketHeatmap** (`src/components/dashboard/charts/MarketHeatmap.tsx`)
   - Visualizes sector/industry performance
   - Needs sector performance data and stock price changes

8. **ComparisonChart** (`src/components/dashboard/charts/ComparisonChart.tsx`)
   - Compares performance of multiple stocks
   - Needs historical data for multiple stocks simultaneously

9. **PortfolioPerformanceChart** (`src/components/dashboard/charts/PortfolioPerformanceChart.tsx`) 
   - Visualizes aggregate watchlist performance
   - Needs historical data for all watchlist stocks

## Data Table Components

10. **AnalystRatingsTable** (`src/components/dashboard/AnalystRatingsTable.tsx`)
    - Displays analyst recommendations and price targets
    - Needs analyst ratings, price targets, and consensus data

11. **InsiderTradesTable** (`src/components/dashboard/InsiderTradesTable.tsx`)
    - Shows recent insider buying and selling activity
    - Needs insider transaction data, filing dates, and trade values

## Dashboard Page Components

12. **Dashboard Page** (`src/app/dashboard/page.tsx`)
    - Main dashboard container
    - Integrates multiple data components

13. **Options Flow Page** (`src/app/dashboard/options-flow/page.tsx`)
    - Shows options trading activity
    - Needs options contracts, premiums, and unusual activity data

14. **Insider Trading Page** (`src/app/dashboard/insider-trading/page.tsx`)
    - Comprehensive insider trading view
    - Needs detailed insider transaction data

15. **Hedge Funds Page** (`src/app/dashboard/hedge-funds/page.tsx`)
    - Shows institutional holdings and 13F filings
    - Needs institutional ownership data and position changes

16. **Analyst Ratings Page** (`src/app/dashboard/analyst-ratings/page.tsx`)
    - Expanded view of analyst opinions
    - Needs detailed analyst ratings and historical rating changes

17. **Technical Analysis Page** (`src/app/dashboard/technical/page.tsx`)
    - Technical indicators and pattern recognition
    - Needs technical indicators, chart patterns, and support/resistance levels

18. **Portfolio Page** (`src/app/dashboard/portfolio/page.tsx`)
    - Watchlist performance tracking
    - Needs aggregate metrics and sector allocation data

19. **Alerts Page** (`src/app/dashboard/alerts/page.tsx`)
    - Configurable price and event alerts
    - Needs price data and event triggers

## Other Components

20. **MarketTicker** (`src/components/MarketTicker.tsx`)
    - Scrolling ticker of market information
    - Needs real-time index data and market movers

21. **AlertTicker** (`src/components/AlertTicker.tsx`)
    - Displays triggered alerts
    - Needs real-time price events and alert configurations

## Data Requirements Summary

| Data Type | Number of Components Requiring |
|-----------|--------------------------------|
| Basic Stock Data (price, change, volume) | 15 |
| Historical Price Data | 8 |
| Technical Indicators | 6 |
| Company Information | 7 |
| Analyst Ratings | 3 |
| Insider Transactions | 3 |
| Options Data | 2 |
| Market Index Data | 5 |
| Sector Performance | 4 |
| News & Events | 5 |

## Priority Components for Integration

Based on user impact and technical feasibility, these components should be prioritized for real data integration:

1. **Watchlist** - Core user experience component
2. **Dashboard Page** - Main entry point with market summary
3. **StockChart** - Critical visualization of price data
4. **MarketIndicators** - Provides market context
5. **AiQueryInterface** - Enhanced with real data context 