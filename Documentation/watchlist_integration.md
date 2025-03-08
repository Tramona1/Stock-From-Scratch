# Watchlist Integration Documentation

## Overview

This document details the implementation of a global watchlist system in our application, enabling all tabs to display data filtered by the user's watchlisted stocks. The system moves away from hardcoded data and implements a real-time, user-specific watchlist that persists across all dashboard sections.

## Latest Updates: Strict Watchlist-based Filtering

The latest update makes a significant change to how data is filtered:

1. **Removal of Toggle**: Previously, tabs had a "Show only watchlist stocks" checkbox that allowed users to see all stocks. This has been removed to ensure a consistent, personalized experience.
2. **Conditional Data Fetching**: Mock data is now only fetched when the watchlist has items, reducing unnecessary API calls.
3. **Strict Empty States**: Empty states are now shown whenever the watchlist is empty, regardless of previous toggle state.
4. **Data Relevance**: All data shown is now guaranteed to be relevant to the user's watchlist, eliminating unrelated information.

This approach ensures that users clearly understand that they need to add stocks to their watchlist to see relevant data throughout the application.

## Implementation Architecture

The watchlist integration follows a React Context-based approach with the following key components:

1. **Watchlist Database Schema**: Stores user-specific watchlist entries in Supabase
2. **WatchlistContext**: A global React Context that manages watchlist state across the application
3. **Watchlist API**: RESTful endpoints for managing watchlist data
4. **Integration with Dashboard Tabs**: Each tab consumes the watchlist data to filter and display relevant information
5. **Empty State Handling**: Consistent empty states when the watchlist is empty

## Database Structure

The watchlist data is stored in a dedicated Supabase table with the following schema:

```sql
CREATE TABLE IF NOT EXISTS public.watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint to prevent duplicate tickers for the same user
ALTER TABLE public.watchlists 
ADD CONSTRAINT watchlists_user_id_ticker_key UNIQUE (user_id, ticker);
```

This schema ensures:
- One-to-many relationship between users and watchlist items
- Unique ticker entries per user (no duplicates)
- Automatic creation timestamps
- Referential integrity with the users table

## WatchlistContext Implementation

The `WatchlistContext` provides a global state management solution for watchlist data, making it accessible across all dashboard pages:

### 1. Context Definition

```typescript
// src/context/WatchlistContext.tsx
interface WatchlistContextType {
  watchlist: WatchlistItem[]
  isLoading: boolean
  isAdding: boolean
  error: string | null
  fetchWatchlist: () => Promise<void>
  addToWatchlist: (ticker: string) => Promise<void>
  removeFromWatchlist: (ticker: string) => Promise<void>
  refreshWatchlist: () => Promise<void>
}
```

### 2. Provider Implementation

The `WatchlistProvider` component:
- Manages the watchlist state
- Provides methods for CRUD operations
- Handles loading and error states
- Integrates with the Watchlist API
- Uses toast notifications for user feedback

### 3. Context Consumption

Components can access the watchlist data using the `useWatchlist` hook:

```typescript
const { watchlist, isLoading, addToWatchlist } = useWatchlist()
```

## API Integration

The watchlist feature uses RESTful API endpoints to interact with the Supabase database:

### 1. GET /api/watchlist

Retrieves the user's watchlist with:
- Authentication via Clerk
- Proper error handling
- Mock price data generation (temporary until real market data is integrated)

### 2. POST /api/watchlist

Adds a ticker to the user's watchlist:
- Validates input
- Prevents duplicates
- Returns updated watchlist with price data
- Provides user feedback via toast notifications

### 3. DELETE /api/watchlist?ticker=AAPL

Removes a ticker from the user's watchlist:
- Uses query parameters for ticker identification
- Returns the updated watchlist
- Provides user feedback

## Empty State Handling

We've implemented comprehensive empty state handling across all dashboard components when a user's watchlist is empty:

### 1. Main Dashboard Empty State

When a user has no stocks in their watchlist, the dashboard displays:
- A prominent message encouraging the user to add stocks
- Clear explanation of the value of adding stocks
- A call-to-action button to add their first stock
- Skeleton/placeholder UI elements are hidden in favor of empty states

```tsx
// Empty state component for the dashboard
const EmptyWatchlistState = () => (
  <Card className="mt-6">
    <CardContent className="text-center flex flex-col items-center py-8">
      <AlertTriangle className="h-12 w-12 text-muted-foreground mb-3" />
      <CardTitle className="mb-2">No Stocks in Your Watchlist</CardTitle>
      <CardDescription className="max-w-md mx-auto mb-4">
        Add stocks to your watchlist to see personalized market data, 
        insights, and analysis across all dashboard tabs.
      </CardDescription>
      <Button variant="outline" className="gap-2">
        <PlusCircle className="h-4 w-4" />
        Add Your First Stock
      </Button>
    </CardContent>
  </Card>
);
```

### 2. Market Scanner Empty State

The Market Scanner component displays:
- An empty state message explaining that scanning requires watchlist stocks
- Disabled input fields and buttons
- A visual indicator (alert icon) to draw attention
- Dimmed UI elements to indicate inactive functionality

### 3. AI Assistant Empty State

The AI Finance Assistant adapts to the empty watchlist by:
- Changing its initial welcome message to guide users to add stocks
- Displaying a "Limited functionality" badge
- Providing specific feedback when users ask questions without a watchlist
- Changing the input placeholder to encourage watchlist additions

### 4. Hedge Funds Tab Empty State

The Hedge Funds page:
- Shows a clear empty state message when no watchlist items exist
- Prevents any data from being displayed when the watchlist is empty
- Displays specific messages for each section (holdings, activity, etc.)

## Integration with Dashboard Tabs

Each dashboard tab now integrates with the watchlist to show relevant data:

### Hedge Funds Tab

The Hedge Funds page:
- Uses `useWatchlist()` to access watchlist data
- Only fetches and displays data for stocks in the watchlist
- Shows empty states when either the watchlist is empty or no matching data is found
- Optimizes performance by not fetching data when watchlist is empty

```typescript
// Conditional data fetching based on watchlist
useEffect(() => {
  const fetchData = async () => {
    setIsLoading(true)
    try {
      const data = await fetchHedgeFundData()
      setHedgeFundData(data)
    } catch (error) {
      console.error("Error fetching hedge fund data:", error)
    } finally {
      setIsLoading(false)
    }
  }

  // Only fetch data if the watchlist has items
  if (watchlist.length > 0) {
    fetchData()
  } else {
    setIsLoading(false)
    setHedgeFundData([])
    setFilteredData([])
  }
}, [watchlist])
```

### Dashboard Overview

The main dashboard:
- Shows general market indicators regardless of watchlist status
- Displays personalized data sections only when the watchlist has stocks
- Shows appropriate loading states during data fetching
- Displays an empty state CTA when the watchlist is empty

### Standard Pattern for All Tabs

Each tab now follows a consistent pattern:
1. Access watchlist data via `useWatchlist()`
2. Only fetch data when watchlist has items
3. Filter data to only show watchlist-relevant information
4. Display appropriate states for:
   - Loading
   - Empty watchlist
   - No matching data for watchlist items 
   - Data found for watchlist items

## Data Flow

The watchlist data flow is as follows:

1. **User Action**: User adds/removes a ticker via the UI
2. **Context Action**: `addToWatchlist`/`removeFromWatchlist` method is called
3. **API Request**: Request is sent to the appropriate API endpoint
4. **Database Update**: Supabase database is updated
5. **Response Processing**: API returns updated watchlist data
6. **State Update**: Context updates the global watchlist state
7. **UI Update**: All components consuming the context re-render with new data
8. **User Feedback**: Toast notifications inform the user of the action result

## Empty State UX Design Principles

Our empty state implementation follows these key design principles:

1. **Informative**: Clearly communicate why the component is empty
2. **Actionable**: Provide a clear path forward for the user
3. **Consistent**: Use similar design patterns across all components
4. **Non-Disruptive**: Empty states should not feel like errors
5. **Educational**: Teach users about the application's functionality
6. **Visually Distinct**: Use icons and spacing to make empty states stand out
7. **Encouraging**: Motivate users to take the next step

## Mock Data vs. Real Data

Current implementation includes mock data generation for stock prices. In the future, this will be replaced with:

1. Real-time market data from external APIs
2. Scheduled data collection for historical prices
3. Proper stock information database tables

The mock data generator functions will be replaced with real API calls without changing the interface, making the transition seamless.

## Usage Example

Here's how a component can integrate with the watchlist system:

```tsx
import { useWatchlist } from "@/context/WatchlistContext"

function MyComponent() {
  const { 
    watchlist, 
    isLoading, 
    addToWatchlist, 
    removeFromWatchlist 
  } = useWatchlist()

  // Only fetch data when needed
  useEffect(() => {
    if (watchlist.length > 0) {
      fetchMyData()
    } else {
      // Clear data when watchlist is empty
      setMyData([])
    }
  }, [watchlist])

  // Filter data based on watchlist
  const filteredData = myData.filter(item => 
    watchlist.some(stock => stock.symbol === item.ticker)
  )

  return (
    <div>
      {isLoading ? (
        <LoadingSpinner />
      ) : watchlist.length === 0 ? (
        <EmptyState message="Add stocks to your watchlist" />
      ) : filteredData.length === 0 ? (
        <NoResultsState message="No data for your watchlist stocks" />
      ) : (
        <DataTable data={filteredData} />
      )}
    </div>
  )
}
```

## Benefits of This Approach

1. **Data Consistency**: Single source of truth for watchlist data
2. **Code Reusability**: Eliminate duplicate data fetching logic
3. **Global State**: All components have access to the same watchlist data
4. **Separation of Concerns**: Context handles state, components handle display
5. **Optimized Performance**: Reduced API calls with shared data
6. **Improved UX**: Consistent user experience across all dashboard tabs
7. **Easy Testing**: Simplified testing with a single mock context
8. **Clear User Guidance**: Empty states guide users toward proper app usage
9. **Reduced Data Load**: Only fetch and process data when needed

## Next Steps

1. **Real Market Data**: Integrate real-time market data API
2. **Watchlist Presets**: Allow users to create multiple watchlists
3. **Additional Tabs**: Complete the integration with all dashboard tabs
4. **Enhanced Filtering**: Add advanced filtering options based on watchlist data
5. **Performance Tracking**: Add performance metrics for watchlisted stocks
6. **Onboarding Flow**: Create a guided experience for new users to build their first watchlist 