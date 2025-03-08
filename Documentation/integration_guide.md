# Financial Data Integration System: Complete Integration Guide

This document provides a comprehensive guide for integrating and maintaining the entire financial data system, from data collection to user interface.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Setup and Configuration](#setup-and-configuration)
3. [Data Flow Pipeline](#data-flow-pipeline)
4. [Authentication Integration](#authentication-integration)
5. [Watchlist System](#watchlist-system)
6. [AI Query System](#ai-query-system)
7. [Adding New Data Types](#adding-new-data-types)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)

## System Architecture Overview

Our system consists of three main components:

### 1. Python Data Collection Backend
- Fetches data from financial APIs (Alpha Vantage, Unusual Whales, etc.)
- Processes and normalizes data
- Stores data in Supabase
- Includes specialized fetchers for technical indicators, forex rates, and commodities

### 2. Supabase Database
- Centralized storage for all financial data
- Authentication integration with Clerk
- Row-level security for user data
- Real-time capabilities (future)

### 3. Next.js Frontend
- User interface for viewing financial data
- Watchlist functionality
- AI query interface
- Authentication with Clerk
- Payment processing with Stripe

### Architectural Diagram

```
┌─────────────────────┐         ┌─────────────────┐         ┌───────────────────┐
│  Financial APIs     │         │  Python Data    │         │  Supabase Database│
│  (Unusual Whales,   │ ───────►│  Fetchers       │ ───────►│  (Postgres)       │
│   Alpha Vantage)    │         │                 │         │                   │
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

## Setup and Configuration

### Environment Variables

The system requires the following environment variables:

#### Next.js Frontend (.env)
```
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Authentication (Clerk)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_DOMAIN=your_clerk_domain

# Payment Processing (Stripe)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# AI Integration
GEMINI_API_KEY=your_gemini_api_key
```

#### Python Backend (.env)
```
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# API Keys
API_KEY_UNUSUAL_WHALES=your_unusual_whales_key
API_KEY_ALPHA_VANTAGE=your_alpha_vantage_key
FRED_API_KEY=your_fred_api_key

# Notifications
SENDGRID_API_KEY=your_sendgrid_key
ADMIN_EMAIL=alerts@yourdomain.com
```

### Deployment Options

The system can be deployed in several ways:

1. **Docker (Recommended)**
   - Use the provided docker-compose.yml file
   - Builds both Next.js and Python components
   - Includes health monitoring API

2. **Manual Deployment**
   - Deploy Next.js to Vercel/Netlify
   - Deploy Python services to a VPS/dedicated server
   - Configure a systemd service for the Python scheduler

3. **Serverless**
   - Deploy Next.js to Vercel
   - Convert Python fetchers to serverless functions (AWS Lambda, etc.)
   - Schedule using CloudWatch Events/Cloud Scheduler

## Data Flow Pipeline

### 1. Data Collection Process

The data collection process follows these steps:

1. **Scheduler Trigger**
   - The scheduler (`python/scheduler.py`) triggers data fetchers on predefined intervals
   - Different data types have different update frequencies based on volatility and API limits

2. **API Requests**
   - Data fetchers make API requests to financial data providers
   - Rate limiting and error handling are applied
   - API responses are validated

3. **Data Processing**
   - Raw API responses are processed and normalized
   - Data is transformed to match database schema
   - Validation ensures data quality
   - Timezone handling ensures consistent datetime comparisons

4. **Deduplication**
   - Duplicate checking prevents storing the same data twice
   - Unique constraints in database tables enforce uniqueness
   - Upsert operations (`on_conflict`) ensure data is updated correctly

5. **Database Insertion**
   - Processed data is inserted into Supabase tables
   - Insert operations use the service role key to bypass RLS

### 2. Watchlist-Driven Data Fetching

For efficiency, the system prioritizes data for stocks in users' watchlists:

1. The scheduler periodically fetches all unique tickers from the `watchlists` table
2. Data fetchers can filter API requests to focus on these symbols
3. When new symbols are added to watchlists, relevant data is fetched on the next scheduler run

### 3. Implemented Data Fetchers

Our system includes the following specialized data fetchers:

1. **Technical Indicators Fetcher** (`fetch_technical_indicators.py`)
   - Retrieves technical analysis indicators like MACD and RSI
   - Supports multiple timeframes (daily, weekly, monthly)
   - Stores indicators with their respective dates for time series analysis
   - Database table: `technical_indicators`

2. **Forex Information Fetcher** (`fetch_forex_info.py`)
   - Collects exchange rate data for currency pairs (e.g., EUR:USD, JPY:USD)
   - Retrieves live exchange rates and historical time series
   - Formats data with bid/ask prices and open/close values
   - Database table: `forex_info`

3. **Commodity Information Fetcher** (`fetch_commodity_info.py`)
   - Gathers price data for commodities like WTI oil, Brent oil, copper, natural gas
   - Collects daily, weekly, and monthly prices
   - Includes unit of measurement and timestamp information
   - Database table: `commodity_info`

4. **Crypto Information Fetcher** (`fetch_crypto_info.py`)
   - Retrieves cryptocurrency data (e.g., BTC, ETH)
   - Collects market cap, volume, and price information
   - Database table: `crypto_info`

5. **Market News Fetcher** (`fetch_market_news.py`)
   - Collects news articles and sentiment data related to stocks
   - Supports filtering by ticker symbols and topics
   - Database tables: `market_news` and `news_sentiment`

### 4. Frontend Data Retrieval

Frontend components follow this process for displaying data:

1. Component mounts and gets watchlist symbols from context
2. Supabase queries filter data based on these symbols
3. UI renders data with appropriate loading/error/empty states
4. Pagination handles large result sets efficiently

## Authentication Integration

Our system uses Clerk for authentication with Supabase integration:

### 1. User Registration and Login Flow

1. User registers or logs in via Clerk
2. On successful auth, Clerk webhook triggers a user creation in Supabase
3. User ID from Clerk is used as the Supabase user ID
4. User-specific data like watchlists are tied to this ID

### 2. Clerk-Supabase Integration

The integration works through these components:

1. **Webhook Handling**:
   - `/api/webhooks/clerk/route.ts` processes Clerk webhook events
   - Creates/updates user records in Supabase

2. **Server-Side Authentication**:
   - `getAuth()` from Clerk provides user ID in API routes
   - This ID is used for Supabase operations

3. **Client-Side Authentication**:
   - Clerk provides the `useUser()` hook for client components
   - The user ID is used to authorize Supabase queries

## Watchlist System

The watchlist system is a central feature connecting different parts of the application:

### 1. Database Structure

```sql
CREATE TABLE public.watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prevent duplicate entries per user
ALTER TABLE public.watchlists ADD CONSTRAINT watchlists_user_id_ticker_key UNIQUE (user_id, ticker);

-- Row-level security
CREATE POLICY watchlist_access_policy ON public.watchlists
  FOR ALL
  USING (user_id = auth.uid()::TEXT);
```

### 2. WatchlistContext Provider

The `WatchlistContext` (`src/context/WatchlistContext.tsx`) provides:

1. Central management of watchlist state
2. Functions for adding/removing tickers
3. Loading and error states
4. Automatic refreshing

### 3. API Routes

Watchlist operations are managed through these API routes:

- `GET /api/watchlist` - Retrieve user's watchlist
- `POST /api/watchlist` - Add a ticker to the watchlist
- `DELETE /api/watchlist?ticker=AAPL` - Remove a ticker

### 4. Integration with Data Components

Data components check the watchlist state to:

1. Filter displayed data to watchlist stocks
2. Show appropriate empty states
3. Adapt UI based on watchlist content

### 5. Data Fetching Optimization

The watchlist system optimizes data fetching by:

1. Prioritizing watchlisted symbols in the fetch queue
2. Updating watchlisted data more frequently
3. Pre-fetching data for newly added watchlist items
4. Using the extended data (technical indicators, forex, commodities) to enhance insights

## AI Query System

The AI Query System allows users to ask natural language questions about their watchlist data:

### 1. Architecture

```
┌───────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Query   │───►│ Context Builder │───►│  Google Gemini  │
│  Component    │    │                 │    │  AI Model       │
└───────────────┘    └────────┬────────┘    └────────┬────────┘
                              │                      │
                     ┌────────▼────────┐    ┌────────▼────────┐
                     │ Supabase Query  │    │ Response        │
                     │ Builder         │    │ Formatter       │
                     └─────────────────┘    └─────────────────┘
```

### 2. Implementation Components

1. **AiQueryInterface Component** (`src/components/dashboard/AiQueryInterface.tsx`)
   - Provides the chat interface
   - Manages conversation history
   - Displays data source badges

2. **AI Query API** (`src/app/api/ai/query/route.ts`)
   - Extracts entities from queries (ticker symbols, data types)
   - Builds contextual data from Supabase
   - Communicates with Gemini API
   - Formats responses

3. **Data Extraction Functions**
   - `extractSymbols()` - Identifies ticker symbols in queries
   - `extractDataTypes()` - Identifies requested data types
   - `formatDataForContext()` - Prepares data for the AI model

### 3. Query Handling Process

1. User enters a query in the chat interface
2. Frontend sends query, watchlist symbols, and chat history to API
3. API extracts entities and retrieves relevant data from Supabase
4. Data is formatted and sent as context to Gemini API
5. Gemini response is returned to frontend with source information
6. Frontend displays the response with appropriate sourcing

### 4. Technical Indicators Integration

The AI query system can now answer questions about technical indicators:

- "What is the RSI for AAPL right now?"
- "Show me stocks with MACD crossovers"
- "Compare the RSI values for my watchlist stocks"

### 5. Forex and Commodity Integration

The system can also answer questions about forex and commodity data:

- "What's the current EUR to USD exchange rate?"
- "How has the price of WTI oil changed this week?"
- "Compare Brent and WTI oil prices"

## Adding New Data Types

To add a new data type to the system, follow these steps:

### 1. Database Table Creation

Create a new table in Supabase:

```sql
CREATE TABLE public.new_data_type (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol TEXT NOT NULL,
  -- Add specific fields for this data type
  value NUMERIC,
  description TEXT,
  date TIMESTAMP WITH TIME ZONE,
  -- Common fields
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add appropriate indexes
CREATE INDEX idx_new_data_type_symbol ON public.new_data_type(symbol);
CREATE INDEX idx_new_data_type_date ON public.new_data_type(date);
```

### 2. Python Fetcher Implementation

Create a new fetcher in `python/fetch_new_data_type.py`:

```python
import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("new_data_type_fetcher")

class NewDataTypeFetcher:
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # API configuration
        self.api_key = os.environ.get("API_KEY_FOR_NEW_DATA")
        self.api_url = "https://api.provider.com/new_data_endpoint"
        
        # Last API call tracking for rate limiting
        self.last_api_call = datetime.min.replace(tzinfo=timezone.utc)
        self.min_api_interval = 1.0  # seconds
        
    def should_update_info(self, identifier: str) -> bool:
        # Check if we should update this item based on recency
        try:
            result = self.supabase.table("new_data_type").select("fetched_at").eq("identifier", identifier).execute()
            
            if result.data and len(result.data) > 0:
                # Convert the fetched_at string to a timezone-aware datetime
                fetched_date = datetime.fromisoformat(result.data[0]["fetched_at"]).replace(tzinfo=timezone.utc)
                
                # Define the update threshold (e.g., 6 hours)
                update_threshold = datetime.now(timezone.utc) - timedelta(hours=6)
                
                # If the data is newer than the threshold, skip the update
                if fetched_date > update_threshold:
                    logger.info(f"Data for {identifier} is recent, skipping update")
                    return False
            
            # If we don't have data or it's older than the threshold, update it
            return True
        except Exception as e:
            logger.error(f"Error checking if {identifier} needs update: {str(e)}")
            # Default to updating if there's an error
            return True
        
    def fetch(self, identifier: str):
        # Implement API fetching logic with rate limiting
        current_time = datetime.now(timezone.utc)
        time_since_last_call = (current_time - self.last_api_call).total_seconds()
        
        if time_since_last_call < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last_call
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Make the API request
        response = requests.get(
            self.api_url,
            params={"identifier": identifier, "apikey": self.api_key}
        )
        
        self.last_api_call = datetime.now(timezone.utc)
        
        # Check for errors and return the data
        response.raise_for_status()
        return response.json()
        
    def process(self, raw_data):
        # Process and normalize the data
        processed_data = {
            "identifier": raw_data["identifier"],
            "value": float(raw_data["value"]),
            "description": raw_data["description"],
            "date": raw_data["date"],
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        return processed_data
        
    def store(self, processed_data):
        # Store data in Supabase with upsert
        response = self.supabase.table("new_data_type").upsert(
            processed_data,
            on_conflict="identifier"
        ).execute()
        
        if response.data:
            logger.info(f"Successfully updated data for {processed_data['identifier']}")
            return True
        else:
            logger.error(f"Failed to update data for {processed_data['identifier']}")
            return False
        
    def run(self, identifiers=None):
        try:
            success_count = 0
            failure_count = 0
            
            if not identifiers:
                identifiers = ["DEFAULT1", "DEFAULT2", "DEFAULT3"]
                
            for identifier in identifiers:
                if self.should_update_info(identifier):
                    try:
                        raw_data = self.fetch(identifier)
                        processed_data = self.process(raw_data)
                        if self.store(processed_data):
                            success_count += 1
                        else:
                            failure_count += 1
                    except Exception as e:
                        logger.error(f"Error processing {identifier}: {str(e)}")
                        failure_count += 1
                else:
                    # Skip but count as success since it's up-to-date
                    success_count += 1
                        
            logger.info(f"Completed run. Success: {success_count}, Failed: {failure_count}")
            
            return {
                "status": "success" if failure_count == 0 else "partial_success",
                "processed": len(identifiers),
                "successful": success_count,
                "failed": failure_count
            }
        except Exception as e:
            logger.error(f"Error in fetcher run: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
```

### 3. Update Scheduler

Add the new fetcher to the scheduler:

```python
# In python/scheduler.py
FETCHERS["new_data_type"] = "python/fetch_new_data_type.py"
DEFAULT_INTERVALS["new_data_type"] = "12h"  # Set appropriate interval
```

### 4. Frontend Component Creation

Create a React component to display the data:

```tsx
// src/components/dashboard/NewDataTypeTable.tsx
"use client"

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWatchlist } from "@/context/WatchlistContext"

// Component implementation with loading/error/empty states
export default function NewDataTypeTable() {
  // Implementation
}
```

### 5. Add to Dashboard

Create a page for the new data type:

```tsx
// src/app/dashboard/new-data-type/page.tsx
"use client"

import NewDataTypeTable from "@/components/dashboard/NewDataTypeTable"
import { Container } from "@/components/ui/Container"

export default function NewDataTypePage() {
  return (
    <Container>
      <h1 className="text-2xl font-bold mb-6">New Data Type</h1>
      <p className="text-muted-foreground mb-6">
        Description of this data type and its significance.
      </p>
      
      <NewDataTypeTable />
    </Container>
  )
}
```

### 6. Update Navigation

Add the new page to the dashboard navigation:

```tsx
// In src/app/dashboard/layout.tsx
const sidebarItems = [
  // Existing items
  {
    name: "New Data Type",
    href: "/dashboard/new-data-type",
    icon: IconComponent
  },
  // Other items
]
```

### 7. AI Integration

Update the AI query system to handle the new data type:

```typescript
// In src/app/api/ai/query/route.ts

// Add to the data type keywords
function extractDataTypes(query: string): string[] {
  const dataTypeKeywords: Record<string, string> = {
    // Existing mappings
    'new keyword': 'new_data_type',
    'another term': 'new_data_type',
    // Other mappings
  };
  // Rest of the function
}

// Add to the format function
function formatDataForContext(type: string, data: any[]): string {
  switch (type) {
    // Existing cases
    case 'new_data_type':
      return `New Data Type:\n${data.map(item => 
        `- ${item.identifier}: ${item.value} on ${new Date(item.date).toLocaleDateString()}`
      ).join('\n')}`;
    // Default case
  }
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Data Not Appearing in Frontend

**Symptoms**: UI shows empty states despite data being in the database

**Potential Causes**:
- Watchlist filtering is excluding the data
- RLS policies are preventing access
- Incorrect Supabase credentials

**Solutions**:
- Check user's watchlist contains relevant symbols
- Verify RLS policies on the table
- Confirm Supabase credentials in env vars

#### 2. Python Fetchers Failing

**Symptoms**: No data updates, scheduler log shows errors

**Potential Causes**:
- API rate limits exceeded
- Invalid API keys
- Network connectivity issues
- Schema changes in API responses
- Timezone handling issues with dates
- Upsert operation format errors

**Solutions**:
- Implement exponential backoff for rate limits
- Verify API keys in .env file
- Check network connectivity
- Update data processing logic if API schema changed
- Ensure datetime objects are timezone-aware before comparison
- Confirm `on_conflict` parameter format matches database constraints

#### 3. Upsert Constraints Failing

**Symptoms**: Database errors about unique constraint violations

**Potential Causes**:
- Incorrect `on_conflict` parameter format
- Missing unique constraints in the database
- Data format mismatch with table schema

**Solutions**:
- Check Supabase table for unique constraints
- Ensure `on_conflict` parameter format is a string with column names separated by commas
- Validate data format before insertion

#### 4. Timezone Issues

**Symptoms**: Incorrect data comparisons or time-based filtering not working

**Potential Causes**:
- Mixing naive and timezone-aware datetime objects
- Not standardizing to UTC for storage
- Timezone conversions not handled properly

**Solutions**:
- Always use timezone-aware datetimes with `datetime.now(timezone.utc)`
- Convert string dates to datetime objects with `.replace(tzinfo=timezone.utc)`
- Store all dates in UTC format in the database

#### 5. AI Query System Not Working

**Symptoms**: AI responses are generic or error messages appear

**Potential Causes**:
- Missing Gemini API key
- No data for the requested symbols/types
- Context size limitations

**Solutions**:
- Verify Gemini API key in env vars
- Check that relevant data exists in Supabase
- Optimize context size by limiting data sent to the model

## Monitoring and Maintenance

### Health Monitoring

The system includes a health monitoring API that checks:

1. **Scheduler Status**: Is the scheduler process running?
2. **Database Connectivity**: Can we connect to Supabase?
3. **Data Freshness**: When was data last updated?
4. **System Resources**: CPU, memory, and disk usage

### Monitoring Endpoints

- `/health` - Basic health check
- `/health/details` - Detailed system metrics
- `/health/tables` - Database table status

### Maintenance Tasks

1. **Regular Data Validation**
   - Periodically check data quality
   - Ensure no duplicate entries
   - Verify schema consistency

2. **API Rotation**
   - Monitor API usage and limits
   - Have fallback data sources ready
   - Rotate API keys if needed

3. **Database Optimization**
   - Archive old data for performance
   - Review and optimize indexes
   - Check for slow queries

4. **Documentation Updates**
   - Keep this integration guide updated
   - Document changes to APIs or schemas
   - Maintain deployment procedure documentation 