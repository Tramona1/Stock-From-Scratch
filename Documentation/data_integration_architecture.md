# Financial Data Integration Architecture

## System Overview

Our financial data integration system brings together data from various financial data sources, processes it, stores it in a central database, and displays it through a modern web interface. This document outlines the architecture and data flows of this system.

```
┌─────────────────────┐         ┌─────────────────┐         ┌───────────────────┐
│  Financial APIs     │         │  Python Data    │         │  Supabase Database│
│  (Unusual Whales,   │ ───────►│  Fetchers       │ ───────►│  (Postgres)       │
│   Other Sources)    │         │                 │         │                   │
└─────────────────────┘         └─────────────────┘         └──────────┬────────┘
                                                                        │
                                                                        │
                                                                        ▼
┌─────────────────────┐         ┌─────────────────┐         ┌───────────────────┐
│  User's Browser     │         │  Next.js        │         │  Supabase Client  │
│  (Dashboard UI)     │◄────────│  Frontend       │◄────────│  (TypeScript)     │
│                     │         │                 │         │                   │
└─────────────────────┘         └─────────────────┘         └───────────────────┘
```

## Components

### 1. Data Sources

Financial data is sourced from the following providers:

- **Unusual Whales API**:
  - Analyst ratings
  - Insider trading data
  - Options flow
  - Dark pool trading
  - Economic calendar
  - FDA calendar
  - Political trading activity

- **Future Potential Sources**:
  - Alpha Vantage
  - Finnhub
  - News APIs
  - FRED Economic Data
  - SEC Edgar filings

### 2. Python Data Processing Backend

The Python backend consists of specialized data fetcher modules:

- **Individual Fetchers**:
  - `fetch_analyst_ratings.py`: Retrieves and processes analyst upgrades/downgrades
  - `fetch_insider_trades.py`: Gathers insider buying/selling activity
  - `fetch_economic_calendar.py`: Collects economic announcements and events
  - `fetch_fda_calendar.py`: Obtains pharmaceutical FDA approval dates
  - `fetch_options_flow.py`: Captures significant options activity
  - `fetch_political_trades.py`: Tracks trading by politicians
  - `fetch_dark_pool_data.py`: Gathers dark pool trading data
  - `fetch_financial_news.py`: Retrieves and processes financial news

- **Scheduler and Orchestration**:
  - `scheduler.py`: Manages the timing and execution of all data fetchers
  - `unusual_whales_api.py`: Common API interface module for Unusual Whales

Each data fetcher follows a consistent pattern:
1. Fetch data from the API
2. Process and normalize the data
3. Check for duplicates in the database
4. Insert new records into Supabase tables

### 3. Supabase Database Layer

The Supabase database serves as the central repository for all financial data, with tables including:

- `analyst_ratings`: Stock analyst ratings and price targets
- `insider_trades`: Company insider buying and selling activity
- `economic_calendar_events`: Economic announcements and releases
- `fda_calendar_events`: Pharmaceutical regulatory events
- `political_trades`: Congressional and political trading data
- `options_flow`: Options market unusual activity
- `dark_pool_data`: Off-exchange trading activity
- `financial_news`: News articles with sentiment analysis
- `alerts`: User-specific notifications based on financial events

Each table is optimized with indexes for common query patterns, particularly:
- Filtering by ticker symbol
- Sorting by date
- Full-text search (where appropriate)

### 4. Next.js Frontend

The frontend displays the financial data through specialized components:

- **Data Access Components**:
  - `InsiderTradesTable.tsx`: Displays insider trading activity
  - `AnalystRatingsTable.tsx`: Shows analyst upgrades/downgrades
  - `EconomicCalendar.tsx`: Lists upcoming economic events
  - (Additional components for each data type)

- **Key Features**:
  - Filtering based on user's watchlist
  - Pagination for navigating large datasets
  - Sorting and searching capabilities
  - Responsive UI for desktop and mobile
  - Proper loading/error/empty states

## Data Flows

### 1. Data Collection Flow

```
┌───────────────┐     ┌─────────────────┐     ┌────────────────┐
│ Schedule      │────►│ API Request     │────►│ Process &      │
│ Trigger       │     │ with Caching    │     │ Normalize Data │
└───────────────┘     └─────────────────┘     └──────┬─────────┘
                                                     │
┌───────────────┐     ┌─────────────────┐     ┌──────▼─────────┐
│ Confirm Data  │◄────│ Insert New      │◄────│ Check for      │
│ Collection    │     │ Records Only     │     │ Duplicates    │
└───────────────┘     └─────────────────┘     └────────────────┘
```

1. The scheduler triggers a data fetcher at a specified interval
2. The fetcher makes API requests with rate limiting and caching
3. Retrieved data is processed and normalized to match the database schema
4. The fetcher checks for existing records to avoid duplicates
5. Only new records are inserted into the database
6. Results are logged for monitoring and troubleshooting

### 2. Data Retrieval Flow

```
┌───────────────┐     ┌─────────────────┐     ┌────────────────┐
│ User Visits   │────►│ Next.js Page    │────►│ React Component│
│ Dashboard Tab │     │ Loads           │     │ Mounts         │
└───────────────┘     └─────────────────┘     └──────┬─────────┘
                                                     │
┌───────────────┐     ┌─────────────────┐     ┌──────▼─────────┐
│ Display       │◄────│ Apply Watchlist │◄────│ Supabase Query │
│ Data to User  │     │ Filtering       │     │ Executes       │
└───────────────┘     └─────────────────┘     └────────────────┘
```

1. User navigates to a dashboard tab (e.g., Insider Trading)
2. The Next.js page loads and renders the appropriate component
3. Upon mounting, the component fetches data from Supabase
4. The query filters data by the user's watchlist tickers
5. Results are processed and displayed with appropriate UI states

## Key Architectural Decisions

### 1. Separation of Concerns

The system maintains clear separation between:
- **Data Collection**: Python backend services
- **Data Storage**: Supabase database
- **Data Presentation**: Next.js frontend

This architecture allows each layer to evolve independently and enables specialized optimizations.

### 2. Real-time vs. Batch Processing

- **Batch Approach**: Most financial data is processed on a scheduled basis rather than in real-time
- **Rationale**: 
  - Many financial data points update infrequently (daily or weekly)
  - API rate limits require thoughtful scheduling
  - Reduces system complexity and resource usage

### 3. Client-Side Data Filtering

- **Approach**: Data filtering based on user's watchlist happens at both the database query and client levels
- **Benefits**:
  - Reduces data transfer volumes
  - Improves response times
  - Minimizes server processing
  - Better user experience with immediate UI feedback

### 4. Incremental Data Updates

- **Approach**: The system only fetches and stores new data since the last update
- **Implementation**: Each fetcher tracks timestamps or identifiers to determine what's new
- **Benefits**: 
  - Reduces API calls
  - Speeds up database operations
  - Minimizes duplicate processing

## Scaling Considerations

1. **Database Growth**: As financial data accumulates, consider:
   - Implementing data archiving for older records
   - Adding table partitioning for large tables
   - Setting up data retention policies

2. **API Rate Limits**: As user base grows:
   - Add more sophisticated rate limiting logic
   - Consider premium API tiers for higher quotas
   - Implement request queue systems for high-demand periods

3. **Frontend Performance**:
   - Implement windowing techniques for large data displays
   - Add more granular filtering options
   - Consider implementing server-side rendering for data-heavy pages

## Future Expansion

The modular nature of this architecture allows for easy expansion:

1. **New Data Types**: Add new tables and corresponding fetchers/components

2. **Additional Data Sources**: Integrate more financial APIs by creating new fetcher modules

3. **Enhanced Analytics**: Add data processing pipelines for:
   - Trading signals generation
   - Machine learning predictions
   - Anomaly detection
   - Custom alerts based on data patterns

4. **Real-time Updates**: Implement Supabase realtime subscriptions for specific high-value data

## Security Considerations

1. **API Keys**: Service role key is used only in server-side Python code

2. **Row-Level Security**: Tables have RLS policies to ensure users see only authorized data

3. **Frontend Access**: Client-side components use the restricted anon key with limited permissions

4. **User Data**: Personal watchlists are protected using Supabase RLS

## Conclusion

This architecture provides a robust foundation for collecting, storing, and displaying financial data while maintaining clear separation of concerns and allowing for future expansion. The system is designed to be maintainable, scalable, and secure, providing users with a responsive and data-rich experience. 