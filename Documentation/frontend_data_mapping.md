# Frontend Data Mapping

This document maps all data points collected by our backend to appropriate frontend components, categorizing by UI prominence and display method.

## Primary Data Display Components

These are major components that display data as their primary function, typically occupying significant screen space.

### 1. Watchlist Component (`src/components/dashboard/Watchlist.tsx`)

**Core Data Points:**
- Ticker Symbol
- Company Name
- Current Price
- Price Change and Percentage
- Daily Volume (formatted)
- Last Updated Timestamp

**Implementation Priority:** Highest (Phase 1)
 
### 2. Stock Chart Component (`src/components/dashboard/charts/StockChart.tsx`)

**Core Data Points:**
- Historical Price Data
- Trading Volume
- Date/Time Ranges

**Technical Overlay Data:**
- Moving Averages
- Bollinger Bands
- RSI 
- MACD

**Implementation Priority:** High (Phase 1)

### 3. Market Indicators Component (`src/components/dashboard/MarketIndicators.tsx`)

**Core Data Points:**
- Major Indices (S&P 500, Nasdaq, Dow)
- Index Percentage Changes
- Market Status (Open/Closed)
- Trading Volume Metrics

**Implementation Priority:** High (Phase 1)

### 4. Options Flow Panel (`src/app/dashboard/options-flow/page.tsx`)

**Core Data Points:**
- Option Contract Details (Strike, Expiration) 
- Option Type (Call/Put)
- Premium Values
- Volume and Open Interest
- Sentiment Indicators
- Flow Analysis Metrics

**Implementation Priority:** Medium (Phase 2)

### 5. Insider Trading Table (`src/components/dashboard/InsiderTradesTable.tsx`)

**Core Data Points:**
- Insider Name and Position
- Transaction Type
- Shares Traded and Value
- Filing Date
- Sentiment Indicator

**Implementation Priority:** Medium (Phase 2)

### 6. Analyst Ratings Table (`src/components/dashboard/AnalystRatingsTable.tsx`)

**Core Data Points:**
- Analyst Firm
- Rating (Buy, Sell, Hold)
- Price Target
- Rating Change Indicator
- Date

**Implementation Priority:** Medium (Phase 2)

### 7. News Feed Component

**Core Data Points:**
- News Title
- Source
- Summary
- Published Date
- Sentiment Indicator
- Related Tickers

**Implementation Priority:** Medium (Phase 2)

### 8. Market Heatmap (`src/components/dashboard/charts/MarketHeatmap.tsx`)

**Core Data Points:**
- Sector Performance
- Industry Performance 
- Major Stock Movements

**Implementation Priority:** Medium (Phase 3)

### 9. Portfolio Performance Chart (`src/components/dashboard/charts/PortfolioPerformanceChart.tsx`)

**Core Data Points:**
- Aggregate Watchlist Performance
- Comparison to Market Indices
- Historical Performance Metrics

**Implementation Priority:** Medium (Phase 3)

## Secondary Data Display Elements

These elements display data as part of larger components, typically in a more compact format.

### 1. Stock Detail Card/Modal

**Core Data Points:**
- Company Description
- Sector and Industry
- Market Cap
- 52-Week High/Low
- P/E Ratio
- Beta
- Dividend Yield

**Implementation Priority:** Medium (Phase 2)

### 2. Technical Indicator Panel

**Core Data Points:**
- RSI Value and Chart
- MACD Values and Chart
- Bollinger Band Width
- Technical Signals (Oversold, Overbought, etc.)

**Implementation Priority:** Medium (Phase 2)

### 3. Company Information Section

**Core Data Points:**
- CEO Name
- Headquarters
- Founded Year
- Employee Count
- Company Website
- Logo

**Implementation Priority:** Low (Phase 3)

### 4. Earnings Information Card

**Core Data Points:**
- Next Earnings Date
- Earnings Announcement Time
- Previous Earnings Performance
- Earnings History Chart

**Implementation Priority:** Medium (Phase 3)

### 5. Ownership Information Cards

**Core Data Points:**
- Institutional Ownership Percentage
- Top Institutional Holders
- Recent Institutional Activity
- Insider Ownership Percentage

**Implementation Priority:** Low (Phase 4)

## Tertiary Data Display Elements

These elements show specialized data in compact formats or as supplementary information.

### 1. Economic Calendar Widget

**Core Data Points:**
- Upcoming Economic Reports
- Report Importance
- Previous/Expected Values

**Implementation Priority:** Low (Phase 4)

### 2. FDA Calendar Widget

**Core Data Points:**
- Upcoming FDA Events
- Event Type
- Related Company/Drug

**Implementation Priority:** Low (Phase 4)

### 3. Dark Pool Activity Indicator

**Core Data Points:**
- Off-Exchange Volume Percentage
- Significant Dark Pool Trades

**Implementation Priority:** Low (Phase 4)

### 4. Market Metrics Tooltips

**Core Data Points:**
- Shares Outstanding
- Float
- Average Volume
- Issue Type

**Implementation Priority:** Low (Phase 3)

### 5. Crypto/Forex/Commodity Mini-Widgets

**Core Data Points:**
- Current Exchange Rates
- Daily Change Percentage
- Mini Price Charts

**Implementation Priority:** Low (Phase 4)

## Data Point to Component Mapping Matrix

This matrix maps data points to specific components where they should be displayed.

| Data Point Category | Primary Components | Secondary Elements | Tertiary Elements |
|---------------------|-------------------|-------------------|-------------------|
| **Basic Stock Data** | Watchlist, StockChart | Stock Detail Card, Company Info Section | Market Metrics Tooltips |
| **Technical Indicators** | StockChart | Technical Indicator Panel | - |
| **Options Data** | Options Flow Panel | - | - |
| **Insider Trading** | Insider Trading Table | Ownership Cards | - |
| **Analyst Ratings** | Analyst Ratings Table | Stock Detail Card | - |
| **Dark Pool Data** | - | - | Dark Pool Activity Indicator |
| **Crypto/Forex/Commodities** | - | - | Mini-Widgets |
| **Market News** | News Feed | - | - |
| **Political Trades** | - | Insider Trading Table | - |
| **Economic Data** | Market Indicators | - | Economic Calendar Widget |
| **FDA Calendar** | - | - | FDA Calendar Widget |
| **Hedge Fund Data** | - | Ownership Information Cards | - |

## Implementation Plan by Component

### Phase 1 (Highest Priority)

1. **Watchlist Component**
   - Integrate with `stock_info` and `stock_details` tables
   - Display real price, volume, and change data
   - Show data source and freshness indicators

2. **Stock Chart Component**
   - Implement basic price charting with real data
   - Add simple moving averages overlay
   - Enable timeframe selection (1D, 1W, 1M, etc.)

3. **Market Indicators Component**
   - Display major indices with real data
   - Show market status (open/closed)
   - Implement basic sector performance overview

### Phase 2 (Medium Priority)

4. **Options Flow Panel**
   - Display real options activity
   - Implement sentiment visualization
   - Create premium and volume filtering

5. **Stock Detail Card/Modal**
   - Show comprehensive company information
   - Display key financial metrics
   - Add technical indicators summary

6. **Insider Trading Table**
   - Show real insider transactions
   - Implement filtering by transaction type
   - Add sentiment indicators

7. **Analyst Ratings Table**
   - Display real analyst recommendations
   - Show price target history
   - Add consensus visualization

8. **News Feed Component**
   - Display relevant financial news
   - Implement sentiment indicators
   - Add filtering by ticker

### Phase 3 (Lower Priority)

9. **Market Heatmap**
   - Visualize sector and industry performance
   - Enable drill-down functionality
   - Add performance comparison

10. **Portfolio Performance Chart**
    - Track watchlist performance over time
    - Compare to major indices
    - Add performance metrics

11. **Technical Indicator Panel**
    - Display detailed technical analysis
    - Add multiple indicator visualizations
    - Implement signal detection

12. **Company Information Section**
    - Show comprehensive company profile
    - Add management team information
    - Display company logo and branding

### Phase 4 (Lowest Priority)

13. **Economic Calendar Widget**
    - Show upcoming economic events
    - Highlight high-impact releases
    - Add historical results comparison

14. **FDA Calendar Widget**
    - Display pharmaceutical approval dates
    - Show clinical trial results
    - Add biotech sector performance metrics

15. **Dark Pool Activity Indicator**
    - Visualize off-exchange trading
    - Highlight significant dark pool movements
    - Add historical dark pool volume analysis

16. **Crypto/Forex/Commodity Widgets**
    - Display key alternative market data
    - Add mini price charts
    - Implement correlation analysis with stocks

## Data Density Considerations

When designing components, we should follow these guidelines for data density:

1. **High-Priority Data** should be:
   - Immediately visible without scrolling
   - Displayed in larger text/elements
   - Accompanied by visual indicators (colors, icons)

2. **Medium-Priority Data** should be:
   - Available with minimal interaction (tab, dropdown)
   - Displayed in medium-sized elements
   - Grouped logically with related information

3. **Low-Priority Data** should be:
   - Available on demand (click, hover, expand)
   - Displayed in smaller elements or tooltips
   - Offered as supplementary information

## Responsive Display Strategy

The display strategy should adapt across device sizes:

1. **Desktop View**:
   - Show all primary components
   - Display high and medium-priority data directly
   - Make low-priority data available through interaction

2. **Tablet View**:
   - Focus on high-priority components
   - Collapse medium-priority data into expandable sections
   - Move low-priority data to separate views/tabs

3. **Mobile View**:
   - Show only the most critical data points
   - Stack components vertically
   - Move most secondary and tertiary elements to dedicated screens 