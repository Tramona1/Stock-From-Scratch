# Backend Implementation Progress & Plan

RULES FOR DOCUEMNTATION: DO NOT REMOVE!!; Make sure you are adding very in-depth descriptions everywhere from every single file that's involved to how it's working. This will be used to discuss with our CTO, so make sure that every single thing they could ever need is documented in here with the changes as you are making them

## Recent Updates: User ID Format Compatibility Fix

### Problem Identified

We discovered a critical issue with the integration between Clerk and Supabase:

```
Error updating user subscription: {
  code: '22P02',
  details: null,
  hint: null,
  message: 'invalid input syntax for type uuid: "user_2tjSfDuQApmcxwHRHszCtKZpKGs"'
}
```

The issue stemmed from a fundamental incompatibility:
- Clerk generates user IDs in a string format like `user_2tjSfDuQApmcxwHRHszCtKZpKGs`
- Our Supabase `users` table expected the `id` column to be in UUID format
- When attempting to query or update users with Clerk IDs, Postgres failed to cast the string to UUID

### Solution Implementation

We implemented a multi-layered approach to handle this incompatibility without requiring database schema changes:

1. **SQL Functions to Bypass Type Checking**

   We created two key SQL functions in Supabase:

   ```sql
   -- Function for updating subscriptions with string IDs
   CREATE OR REPLACE FUNCTION update_subscription_with_string_id(
     p_user_id TEXT,
     p_subscription_id TEXT,
     p_subscription_status TEXT,
     p_plan_type TEXT,
     p_is_annual BOOLEAN,
     p_current_period_end TIMESTAMPTZ,
     p_cancel_at_period_end BOOLEAN
   ) RETURNS VOID AS $$
   BEGIN
     UPDATE public.users
     SET 
       subscription_id = p_subscription_id,
       subscription_status = p_subscription_status,
       plan_type = p_plan_type,
       is_annual = p_is_annual,
       current_period_end = p_current_period_end,
       cancel_at_period_end = p_cancel_at_period_end,
       updated_at = NOW()
     WHERE id::TEXT = p_user_id;
   END;
   $$ LANGUAGE plpgsql;
   
   -- Function for retrieving subscription data with string IDs
   CREATE OR REPLACE FUNCTION get_subscription_by_string_id(
     p_user_id TEXT
   ) RETURNS TABLE (
     subscription_status TEXT,
     subscription_id TEXT,
     plan_type TEXT,
     is_annual BOOLEAN,
     current_period_end TIMESTAMPTZ,
     cancel_at_period_end BOOLEAN
   ) AS $$
   BEGIN
     RETURN QUERY
     SELECT 
       u.subscription_status,
       u.subscription_id,
       u.plan_type,
       u.is_annual,
       u.current_period_end,
       u.cancel_at_period_end
     FROM 
       public.users u
     WHERE 
       u.id::TEXT = p_user_id;
   END;
   $$ LANGUAGE plpgsql;
   ```

   The key insight is using `id::TEXT = p_user_id` which compares the UUID column after casting it to text, bypassing the type mismatch.

2. **Enhanced API Endpoints**

   We updated several API endpoints to use these functions:

   - **New Activation Endpoint**: Created `/api/subscriptions/activate` to handle direct subscription activation with Clerk IDs
   - **Updated Subscriptions Endpoint**: Enhanced `/api/subscriptions` to use string ID queries as a fallback

3. **Improved Success Page**

   We modified the success page to actively trigger subscription updates after payment:

   ```typescript
   // src/app/success/page.tsx
   useEffect(() => {
     const updateSubscription = async () => {
       if (!isLoaded || !user) return;
       
       try {
         setIsUpdating(true);
         
         // Call an API to force update the subscription status
         const response = await fetch('/api/subscriptions/activate', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({
             sessionId,
             plan: plan || 'pro',
             isAnnual: isAnnual || false
           }),
         });
         
         // Process response...
       } catch (err) {
         // Error handling...
       } finally {
         setIsUpdating(false);
       }
     };
     
     updateSubscription();
   }, [isLoaded, user, sessionId, plan, isAnnual]);
   ```

4. **Comprehensive Documentation**

   Created `Documentation/supabase_functions.md` with:
   - Detailed explanation of the issue
   - SQL function definitions
   - Implementation instructions
   - Long-term solution options

## Complete Database Schema Update

After implementing the initial solution with custom SQL functions, we discovered a more direct approach was needed to fully resolve the issue. We modified the database schema:

```sql
-- First drop policies that depend on the ID column
DROP POLICY IF EXISTS user_select_own ON public.users;
DROP POLICY IF EXISTS user_access_own_data ON public.users;
DROP POLICY IF EXISTS user_update_own ON public.users;

-- Change column type
ALTER TABLE public.users 
ALTER COLUMN id TYPE TEXT;

-- Recreate policies with TEXT comparison
CREATE POLICY user_access_own_data ON public.users
  FOR ALL
  USING (id = auth.uid()::TEXT);

-- For update-specific policies
CREATE POLICY user_update_own ON public.users
  FOR UPDATE
  USING (id = auth.uid()::TEXT);
```

This schema change allows Clerk's string-formatted user IDs to be stored natively in Supabase without needing type conversions or special handling.

## Removal of Mock Data and Improved Error Handling

To ensure reliability and proper testing, we made the following improvements:

1. **Eliminated Mock Data Fallbacks**
   ```typescript
   // BEFORE:
   if (error) {
     console.error('Error fetching user subscription:', error);
     // Return development fallback data
     if (process.env.NODE_ENV === 'development') {
       console.info('Using mock subscription data for development');
       return {
         status: 'inactive',
         plan: 'free',
         // ...other mock properties
       };
     }
     return null;
   }
   
   // AFTER:
   if (error) {
     console.error('Error fetching user subscription:', error);
     return null;
   }
   ```

2. **Enhanced Error Logging**
   - Added detailed console logs to track data flow
   - Included specific error messages and user IDs

3. **User Existence Verification**
   - Added explicit checks for user existence before operations
   - Added auto-creation of user records when needed
   ```typescript
   // Check if user exists in database first
   const { data: user, error: userError } = await supabase
     .from('users')
     .select('id, email')
     .eq('id', userId)
     .single();
   
   if (userError || !user) {
     console.error('User not found in database:', userId, userError);
     // Create user or handle error...
   }
   ```

## Improved Clerk Webhook

We enhanced the Clerk webhook that creates users in Supabase:

```typescript
// src/app/api/webhooks/clerk/route.ts
case 'user.created': {
  console.log(`Creating Supabase user record for user ${data.id}`);
  
  // Check if the user already exists in Supabase (to prevent duplicates)
  const { data: existingUser, error: checkError } = await supabase
    .from('users')
    .select('id')
    .eq('id', data.id)
    .single();
    
  if (checkError && checkError.code !== 'PGRST116') {
    console.error('Error checking for existing user:', checkError);
    return NextResponse.json({ error: 'Error checking for existing user' }, { status: 500 });
  }
    
  if (existingUser) {
    console.log(`User ${data.id} already exists in Supabase`);
    return NextResponse.json({ success: true, message: 'User already exists' });
  }
  
  // Add user to Supabase with proper TEXT ID support
  const userData = {
    id: data.id, // Clerk string ID format now works directly
    // ...other user properties
  };

  console.log('Inserting user into Supabase:', userData);
  
  const { error } = await supabase.from('users').insert(userData);
  // Error handling...
}
```

This ensures new users are reliably created in the database with their Clerk IDs.

## Complete End-to-End Testing Process

To ensure the subscription system works properly for new users:

1. **Create a New Clerk Account** - Sign up with a new email address
2. **Verify User Creation** - Confirm the user record appears in Supabase (TEXT id format)
3. **Subscribe to a Plan** - Complete the payment process with Stripe
4. **Check Subscription Status** - Verify the user's subscription status updates to "active" in both Supabase and the UI

The system should now work seamlessly for both existing and new users.

## Long-Term Solutions

For a more permanent solution, we've documented several options:

1. **Change the users table to use TEXT for the id column instead of UUID**
   ```sql
   ALTER TABLE public.users 
   ALTER COLUMN id TYPE TEXT;
   ```
   ✅ Implemented this solution as the preferred approach

2. **Create a mapping table between Clerk IDs and UUIDs**
   ```sql
   CREATE TABLE public.user_id_mapping (
     clerk_id TEXT PRIMARY KEY,
     supabase_id UUID NOT NULL UNIQUE
   );
   ```

3. **Use a trigger to automatically handle the conversion**
   ```sql
   CREATE OR REPLACE FUNCTION handle_clerk_id() RETURNS TRIGGER AS $$
   BEGIN
     -- Handle conversion logic here
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;
   
   CREATE TRIGGER clerk_id_trigger
   BEFORE INSERT OR UPDATE ON public.users
   FOR EACH ROW EXECUTE FUNCTION handle_clerk_id();
   ```

### Implementation Requirements

To implement this fix, run the following steps:

1. Log in to your Supabase dashboard
2. Open the SQL Editor
3. Run the SQL to modify the column type and policies
4. Deploy the updated API routes and success page
5. Test the complete payment flow

## Environment Configuration

### Required Environment Variables

For Supabase integration, the following environment variables are required:

```bash
# Required for both client and server
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Required for server-side operations
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### Environment Fallbacks for Development

To ensure smooth development, the application implements fallback mechanisms when environment variables are missing:

1. In development mode, if `SUPABASE_SERVICE_ROLE_KEY` is missing but `NEXT_PUBLIC_SUPABASE_ANON_KEY` is available, the anon key will be used as a fallback.
2. If both keys are missing, a mock Supabase client is used that returns empty data without errors.
3. For subscription data, mock data is returned to enable UI testing without real data.

```typescript
// Fallback logic in server.ts
if (!supabaseKey) {
  console.warn('Missing SUPABASE_SERVICE_ROLE_KEY - using fallback in development mode');
  if (isDev) {
    // In development, use the anon key if available as fallback
    const fallbackKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (fallbackKey) {
      console.info('Using NEXT_PUBLIC_SUPABASE_ANON_KEY as fallback for development');
      return createClientBase<Database>(supabaseUrl, fallbackKey, {/*...*/});
    }
    
    return createMockClient();
  }
}
```

## What Has Been Done ✅

1. **Added Required Dependencies**
   - Installed Supabase client for database interactions
   - Added SWR for efficient data fetching and caching

2. **Created Foundational Infrastructure**
   - `src/lib/supabase.ts`: Configured client-side Supabase client connection with proper type safety
   - `src/lib/supabase/server.ts`: Implemented server-side Supabase client with caching and service role access
   - `src/services/api.ts`: Established external API service layer for Alpha Vantage, FRED, and Unusual Whales
   - `src/services/database.ts`: Created Supabase database service layer with CRUD operations
   - `src/services/users.ts`: Added user service layer for Supabase operations related to users and subscriptions
   - `src/types/api.ts`: Defined comprehensive type interfaces for API/database responses
   - `src/types/supabase.ts`: Created TypeScript definitions for Supabase database schema

3. **Integrated Authentication with Database**
   - Implemented Clerk webhook handler to synchronize users with Supabase
   - Set up proper user creation, updating, and deletion in Supabase
   - Created verification and signature checking for webhooks

4. **Connected Subscription System with Database**
   - Updated subscription management endpoints to use Supabase for data storage
   - Connected Stripe webhooks to update subscription information in Supabase
   - Implemented subscription status tracking and changes

5. **Created Custom Hooks for Data Access**
   - Implemented `useSubscription` hook for accessing and updating subscription data
   - Used SWR for efficient data fetching and caching
   - Added helper functions for subscription status checks and actions

6. **Updated First Component**
   - `MarketIndicators.tsx`: Converted from hard-coded data to real data with proper loading/error states

## Current Implementation Details

### Database Schema

The application uses the following Supabase tables:

1. **users**
   ```sql
   CREATE TABLE public.users (
     id UUID PRIMARY KEY, -- Clerk user ID
     email TEXT UNIQUE NOT NULL,
     first_name TEXT,
     last_name TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     subscription_status TEXT DEFAULT 'inactive',
     subscription_id TEXT,
     stripe_customer_id TEXT,
     plan_type TEXT DEFAULT 'free',
     is_annual BOOLEAN DEFAULT false,
     current_period_end TIMESTAMP WITH TIME ZONE,
     cancel_at_period_end BOOLEAN DEFAULT false
   );
   
   -- Add row-level security policy
   ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
   
   -- Only allow users to see their own data
   CREATE POLICY user_access_own_data ON public.users
     FOR ALL
     USING (id = auth.uid());
   ```

2. **watchlists**
   ```sql
   CREATE TABLE public.watchlists (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
     ticker TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Add row-level security policy
   ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
   
   -- Only allow users to see their own watchlist items
   CREATE POLICY watchlist_access_policy ON public.watchlists
     FOR ALL
     USING (user_id = auth.uid()::TEXT);
   ```

### Supabase Client Configuration

#### Client-Side Configuration

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';

// Environment variables for client-side Supabase access
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

// Create and export the Supabase client
export const supabase = createClient<Database>(
  supabaseUrl || '',
  supabaseAnonKey || '',
  {
    auth: {
      persistSession: true,
    },
  }
);
```

#### Server-Side Configuration

```typescript
// src/lib/supabase/server.ts
import { createClient as createClientBase } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';

// Cache the Supabase client to avoid creating a new client for every call
let supabaseClient: ReturnType<typeof createClientBase<Database>> | null = null;

/**
 * Creates a Supabase client with the service role key for server operations
 */
export function createClient() {
  // Return the cached client if it exists
  if (supabaseClient) {
    return supabaseClient;
  }
  
  // Create a new client with the service role key
  supabaseClient = createClientBase<Database>(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
    },
  });
  
  return supabaseClient;
}
```

### Authentication Flow

1. User signs up through Clerk authentication
2. Clerk webhook triggers creation of user record in Supabase
3. User ID from Clerk is used as the primary key in Supabase
4. Server-side API routes authenticate with Clerk and then access Supabase data

### Subscription Management

1. User initiates a subscription through the checkout process
2. The API creates a Stripe checkout session 
3. After successful payment, Stripe webhook updates the user's subscription in Supabase
4. Subscription status and details are stored in the users table
5. API endpoints for cancellation and reactivation update both Stripe and Supabase

### Custom Hooks

The `useSubscription` hook provides a clean interface for components to access subscription data:

```typescript
// src/hooks/useSubscription.ts
export function useSubscription() {
  const { isSignedIn, user } = useUser();
  const [hasMounted, setHasMounted] = useState(false);
  
  // Only start fetching after component mounts to avoid hydration issues
  useEffect(() => {
    setHasMounted(true);
  }, []);
  
  // Don't fetch if not signed in or component hasn't mounted yet
  const shouldFetch = isSignedIn && hasMounted;
  
  const { data, error, isLoading, mutate } = useSWR(
    shouldFetch ? '/api/subscriptions' : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60000, // 1 minute
    }
  );
  
  // Extract subscription from response or use default
  const subscription = data?.subscription || defaultSubscription;
  
  // Helper method example with date validation
  const daysRemaining = (): number | null => {
    if (!subscription.currentPeriodEnd) return null;
    
    const endDate = new Date(subscription.currentPeriodEnd);
    
    // Check for invalid dates (like epoch 0 or very old dates)
    if (isNaN(endDate.getTime()) || endDate.getFullYear() < 2000) {
      return null;
    }
    
    const now = new Date();
    const diffTime = endDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
  };
  
  return {
    subscription,
    isLoading,
    error,
    isSubscribed,
    isCancelling,
    daysRemaining,
    cancelSubscription,
    reactivateSubscription,
    mutate,
  };
}
```

### Data Validation Strategies

The application employs several strategies to ensure data integrity:

1. **Date Validation**: All date handling includes validation to prevent invalid dates (e.g., 1969 timestamps)
   ```typescript
   // Validate currentPeriodEnd in getUserSubscription
   let currentPeriodEnd = data.current_period_end;
   if (currentPeriodEnd) {
     const date = new Date(currentPeriodEnd);
     if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
       currentPeriodEnd = null;
     }
   }
   ```

2. **Conditional UI Rendering**: Component displays adapt based on data validity and status
   ```typescript
   // Conditional rendering based on subscription status
   {subscription && (
     subscription.status === 'active' ? (
       subscription.cancelAtPeriodEnd ? (
         <Button>Reactivate Subscription</Button>
       ) : (
         <Button>Cancel Subscription</Button>
       )
     ) : (
       <Link href="/pricing">
         <Button>Subscribe Now</Button>
       </Link>
     )
   )}
   ```

3. **Fallback Values**: All API responses include fallback values to handle edge cases
   ```typescript
   // Default fallback response for missing subscriptions
   return NextResponse.json({
     subscription: {
       status: 'inactive',
       plan: 'free',
       isAnnual: false,
       currentPeriodEnd: null,
       cancelAtPeriodEnd: false
     }
   });
   ```

### Data Access Patterns

1. Server-side API routes use `createClient()` to access Supabase with service role
2. Proper error handling ensures reliable database operations
3. Type safety through TypeScript ensures correct data structures
4. Subscriptions are managed with dedicated service functions
5. SWR provides efficient caching and revalidation

## Next Steps to Complete 📝

1. **Update Remaining Components (Priority Order)**
   - Watchlist component (core functionality)
   - Market scanner component (real-time data)
   - Options flow and hedge fund components (institutional activity)
   - Charts components (data visualization)

2. **Implement SWR for Additional Data**
   - Expand the SWR pattern to other data types
   - Set up revalidation strategies (interval, on-focus, on-reconnect)
   - Configure optimistic UI updates for better UX

3. **Enhance Error Handling**
   - Implement comprehensive error boundaries
   - Create fallback UI for various error scenarios
   - Add retry mechanisms for transient failures

4. **Optimize Data Flow**
   - Add request throttling for rate-limited APIs
   - Implement data transformers to normalize API responses
   - Set up background data refresh strategies

5. **Testing & Monitoring**
   - Add error logging to capture API/database failures
   - Test integration points with actual data sources
   - Create fallback mock data for development 

## Development vs Production Considerations

### Mock Client Implementation

For development without a Supabase connection, a mock client is provided:

```typescript
function createMockClient() {
  console.info('Creating mock Supabase client for development');
  return {
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: null, error: null }),
          execute: async () => ({ data: [], error: null }),
        }),
        execute: async () => ({ data: [], error: null }),
      }),
      insert: async () => ({ data: null, error: null }),
      update: async () => ({ data: null, error: null }),
      delete: async () => ({ data: null, error: null }),
    }),
  } as any;
}
```

### Development Fallback Data

When Supabase is unavailable or returns an error, mock data is provided in development mode:

```typescript
if (process.env.NODE_ENV === 'development') {
  console.info('Using mock subscription data for development');
  return {
    status: 'inactive',
    plan: 'free',
    isAnnual: false,
    currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    cancelAtPeriodEnd: false,
    subscriptionId: null
  };
}
```

## User-Specific Watchlist Implementation

We've implemented a fully functional user-specific watchlist system that saves each user's stock preferences to Supabase. This replaces the previous mock data with real persistent data tied to the authenticated user.

### Database Structure

The watchlist uses the existing `watchlists` table in Supabase:

```sql
CREATE TABLE public.watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id STRING REFERENCES public.users(id) ON DELETE CASCADE,
  ticker STRING NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add row-level security policy
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;

-- Only allow users to see their own watchlist items
CREATE POLICY watchlist_access_policy ON public.watchlists
  FOR ALL
  USING (user_id = auth.uid()::TEXT);
```

The table links to the `stock_info` table which provides price, volume, and other data for each ticker.

### API Implementation

We created a new API endpoint at `/api/watchlist` that handles all watchlist operations:

1. **GET /api/watchlist**: Fetches the user's watchlist
2. **POST /api/watchlist**: Adds a ticker to the watchlist
3. **DELETE /api/watchlist?ticker=AAPL**: Removes a ticker from the watchlist

The API ensures:
- Authentication via Clerk
- User existence in Supabase (auto-creates if missing)
- Error handling with appropriate status codes
- Data transformation to maintain frontend compatibility

Here's a summary of the implementation:

```typescript
// GET: Get user's watchlist
export async function GET(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Ensure user exists in Supabase
    await createUserIfNotExists(userId);
    
    // Get watchlist from Supabase
    const watchlistItems = await getUserWatchlist(userId);
    
    // Transform data for frontend compatibility
    const transformedWatchlist = watchlistItems.map(item => ({
      id: item.id,
      symbol: item.ticker,
      price: item.stock_info?.current_price || 0,
      change: item.stock_info?.change_percent || 0,
      volume: item.stock_info?.marketcap ? 
        `${(item.stock_info.marketcap / 1000000).toFixed(1)}M` : 'N/A',
      watching: true
    }));

    return NextResponse.json({ 
      success: true, 
      watchlist: transformedWatchlist
    });
  } catch (error) {
    // Error handling
  }
}
```

### UI Component Updates

The `Watchlist` component was completely refactored to:

1. Use real API data instead of mock data
2. Handle loading, error, and empty states
3. Provide feedback with toast notifications
4. Support keyboard input (Enter to add ticker)
5. Show different UI for authenticated vs non-authenticated users

Key features include:
- Automatic watchlist loading when a user is authenticated
- Real-time addition and removal of tickers
- Cache control headers to prevent stale data
- Optimistic UI updates for better user experience

```typescript
export function Watchlist() {
  const { isLoaded, isSignedIn, user } = useUser();
  const [userWatchlist, setUserWatchlist] = useState<WatchlistItem[]>([]);
  const [newTickerInput, setNewTickerInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch watchlist when component mounts
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    fetchWatchlist();
  }, [isLoaded, isSignedIn]);
  
  // API integration methods
  const fetchWatchlist = async () => {/* API call */};
  const addToWatchlist = async (ticker: string) => {/* API call */};
  const removeFromWatchlist = async (ticker: string) => {/* API call */};
  
  // Conditional rendering based on auth state and data status
  if (isLoaded && !isSignedIn) {
    return <AuthPromptCard />;
  }
  
  return (
    <Card>
      {/* UI for adding tickers */}
      {/* Conditional rendering for loading/error/empty states */}
      {/* Mapped list of watchlist items */}
    </Card>
  );
}
```

### Database Service Updates

The server-side database service already had methods for watchlist operations:

```typescript
// Get user's watchlist with stock info
export async function getUserWatchlist(userId: string): Promise<WatchlistItem[]> {
  const { data, error } = await supabase
    .from('watchlists')
    .select('*, stock_info(*)')
    .eq('user_id', userId);
  
  if (error) throw error;
  return data || [];
}

// Add ticker to user's watchlist
export async function addToWatchlist(userId: string, ticker: string): Promise<void> {
  const { error } = await supabase
    .from('watchlists')
    .insert({ user_id: userId, ticker });
  
  if (error) throw error;
}

// Remove ticker from user's watchlist
export async function removeFromWatchlist(userId: string, ticker: string): Promise<void> {
  const { error } = await supabase
    .from('watchlists')
    .delete()
    .eq('user_id', userId)
    .eq('ticker', ticker);
  
  if (error) throw error;
}
```

### Integration with Clerk Authentication

The watchlist system seamlessly integrates with Clerk for authentication:

1. Each API request gets the `userId` from Clerk using `getAuth(req)`
2. The API verifies if a user has a record in Supabase using `createUserIfNotExists()`
3. All database operations use the userId as a key to maintain per-user data

This approach ensures:
- Data security (users can only access their own watchlist)
- Consistent user experience across devices
- Reliable data persistence

### Error Handling and Edge Cases

The implementation handles several edge cases:

1. **Unauthenticated users**: Shows a sign-in prompt
2. **Network errors**: Displays error message with retry option
3. **Duplicate tickers**: Prevents adding the same ticker twice
4. **Empty watchlist**: Shows an empty state message
5. **Missing stock data**: Provides fallback values

### Testing Strategy

To test the watchlist implementation:

1. Sign in with a test account
2. Add several tickers to the watchlist
3. Verify they appear in the UI
4. Reload the page to confirm persistence
5. Remove some tickers and verify they're deleted
6. Sign out and confirm the watchlist shows the authentication prompt
7. Sign in with a different account to verify a separate watchlist

### Next Steps

Future enhancements for the watchlist:

1. **Real-time updates**: Implement web sockets for real-time price updates
2. **Multiple watchlists**: Allow users to create and manage multiple watchlists
3. **Additional data**: Add more stock metrics and performance indicators
4. **Drag and drop reordering**: Allow users to prioritize their watchlist
5. **Export/import capabilities**: Enable sharing or backing up watchlists
6. **Price alerts**: Notify users when stocks reach certain thresholds
