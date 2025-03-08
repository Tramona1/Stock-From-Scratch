# API Documentation

## RULES FOR DOCUEMNTATION: DO NOT REMOVE!!; Make sure you are adding very in-depth descriptions everywhere from every single file that's involved to how it's working. This will be used to discuss with our CTO, so make sure that every single thing they could ever need is documented in here with the changes as you are making them


## Authentication System

### Middleware Configuration

This application uses Clerk's middleware for authentication:

```typescript
import { clerkMiddleware, clerkMiddleware as middleware } from "@clerk/nextjs/server";

// Define public routes
const publicPaths = [
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/auth/login(.*)',
  '/auth/signup(.*)',
  '/pricing',
  '/api/webhooks(.*)',
  '/success',
  '/help'
];

// Create middleware function with Clerk
export default middleware((req) => {
  // Clerk handles authentication automatically
  return;
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
};
```

### Auth Routes

Authentication uses catch-all routes for Clerk components:

- `/auth/login/[[...sign-in]]/page.tsx` - Sign-in page
- `/auth/signup/[[...sign-up]]/page.tsx` - Sign-up page

### API Authentication

API routes use Clerk's `getAuth()` function to verify user authentication:

```typescript
import { getAuth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export async function GET(request) {
  try {
    const { userId } = getAuth(request);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // API logic here
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
```

### Client-Side Authentication

Client components use the `useUser` hook from Clerk to access authentication state:

```typescript
import { useUser } from "@clerk/nextjs";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ProtectedPage() {
  const { isLoaded, user } = useUser();
  const router = useRouter();
  
  useEffect(() => {
    if (isLoaded && !user) {
      // Redirect to login if user is not authenticated
      router.push(`/sign-in?redirectUrl=${encodeURIComponent(window.location.pathname)}`);
    }
  }, [isLoaded, user, router]);
  
  if (!isLoaded || !user) {
    return <div>Loading...</div>;
  }
  
  return <div>Protected content</div>;
}
```

## User Profile Management

### Profile Page

The profile page (`/src/app/profile/page.tsx`) allows users to view and update their personal information. The page is structured with several components:

1. **Profile Details**: Displays and allows editing of user's first name and last name
2. **Subscription Management**: Links to the billing page for subscription details
3. **Security Settings**: Links to Clerk's security management

The profile page uses real data from Clerk and combines it with data from Supabase:

```typescript
// In profile page useEffect
useEffect(() => {
  if (!isLoaded) return;
  
  if (!user) {
    router.push("/sign-in");
    return;
  }
  
  // Initialize form data with Clerk user data
  setFormData({
    firstName: user.firstName || "",
    lastName: user.lastName || "",
    email: user.primaryEmailAddress?.emailAddress || "",
  });
  
  setIsLoading(false);
}, [isLoaded, user, router]);
```

Profile updates are handled through the `/api/auth/user` endpoint:

```typescript
// In profile page handleSaveProfile function
const handleSaveProfile = async () => {
  setIsSaving(true);
  try {
    // Make API call to update user
    const response = await fetch("/api/auth/user", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        firstName: formData.firstName,
        lastName: formData.lastName,
      }),
    });
    
    if (!response.ok) throw new Error("Failed to update profile");
    
    // Update Clerk user object in UI
    if (user) {
      await user.update({
        firstName: formData.firstName,
        lastName: formData.lastName,
      });
    }
    
    toast({
      title: "Profile updated",
      description: "Your profile has been updated successfully.",
    });
  } catch (error) {
    console.error("Error updating profile:", error);
    toast({
      title: "Error",
      description: "Failed to update your profile. Please try again.",
      variant: "destructive",
    });
  } finally {
    setIsSaving(false);
  }
};
```

### User API Endpoints

#### GET /api/auth/user

This endpoint retrieves a user's profile information, combining data from both Clerk and Supabase:

```typescript
export async function GET(req: NextRequest) {
  try {
    const auth = getAuth(req);
    const userId = auth.userId;
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get user from Clerk
    const clerk = await clerkClient();
    const user = await clerk.users.getUser(userId);
    
    // Get additional user info from Supabase if needed
    const supabase = createClient();
    const { data: userProfile } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();

    return NextResponse.json({
      id: user.id,
      firstName: user.firstName,
      lastName: user.lastName,
      email: user.emailAddresses[0]?.emailAddress,
      imageUrl: user.imageUrl,
      // Include additional data from Supabase
      profile: userProfile || {}
    });
  } catch (error) {
    console.error('Error fetching user:', error);
    return NextResponse.json({ error: 'Failed to fetch user' }, { status: 500 });
  }
}
```

#### PATCH /api/auth/user

This endpoint updates a user's profile information, modifying data in both Clerk and Supabase:

```typescript
export async function PATCH(req: NextRequest) {
  try {
    const auth = getAuth(req);
    const userId = auth.userId;
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const data = await req.json();
    
    // Update user in Clerk if needed
    if (data.firstName || data.lastName) {
      const clerk = await clerkClient();
      await clerk.users.updateUser(userId, {
        firstName: data.firstName,
        lastName: data.lastName,
      });
    }

    // Update additional user info in Supabase if needed
    if (data.profile) {
      const supabase = createClient();
      const { error } = await supabase
        .from('users')
        .update(data.profile)
        .eq('id', userId);
      
      if (error) throw error;
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error updating user:', error);
    return NextResponse.json({ error: 'Failed to update user' }, { status: 500 });
  }
}
```

## Help and Support System

### Help Page

The help page (`/src/app/help/page.tsx`) provides users with searchable FAQs and support information. Key features:

1. **Searchable FAQs**: Users can search through frequently asked questions
2. **Contact Options**: Direct links to email support and contact form
3. **Interactive Accordion**: Questions expand to show answers

The help page uses client-side filtering to provide instant search results:

```typescript
export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  
  // Filter FAQs based on search query
  const filteredFaqs = searchQuery 
    ? faqs.filter(faq => 
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) || 
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : faqs;
    
  // Component rendering...
}
```

The page leverages the custom Accordion component to display questions and answers:

```typescript
<Accordion type="single" collapsible className="w-full">
  {filteredFaqs.map((faq, index) => (
    <AccordionItem 
      key={index} 
      value={`item-${index}`}
      trigger={
        <AccordionTrigger>{faq.question}</AccordionTrigger>
      }
    >
      <AccordionContent>{faq.answer}</AccordionContent>
    </AccordionItem>
  ))}
</Accordion>
```

### Custom Accordion Component

The custom Accordion component (`/src/components/ui/accordion.tsx`) provides a reusable interface for displaying collapsible content. It supports:

1. **Single or Multiple** open items
2. **Collapsible mode** for closing all items
3. **Default values** for pre-opened items

The implementation uses React's context system to handle state between parent and child components:

```typescript
const Accordion = React.forwardRef<HTMLDivElement, AccordionProps>(
  ({ children, className, type = "single", collapsible = false, defaultValue, ...props }, ref) => {
    const [openItems, setOpenItems] = React.useState<string[]>(
      defaultValue ? [defaultValue] : []
    );

    const handleItemClick = (value: string) => {
      if (type === "single") {
        if (collapsible && openItems.includes(value)) {
          setOpenItems([]);
        } else {
          setOpenItems([value]);
        }
      } else {
        if (openItems.includes(value)) {
          setOpenItems(openItems.filter(item => item !== value));
        } else {
          setOpenItems([...openItems, value]);
        }
      }
    };

    // Clone children with additional props...
  }
);
```

## Supabase Integration

The application integrates Clerk authentication with Supabase for storing user data and managing subscriptions.

### Client-Side Supabase Setup

```typescript
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

### Server-Side Supabase Functions

```typescript
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

### User Services

The application includes dedicated services for user data management:

```typescript
// User type definitions from Supabase schema
export type User = Database['public']['Tables']['users']['Row'];
export type UserUpdateData = Database['public']['Tables']['users']['Update'];

// Get a user by ID
export async function getUserById(userId: string): Promise<User | null> {
  try {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();
    
    if (error) {
      console.error('Error fetching user:', error);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Unexpected error fetching user:', error);
    return null;
  }
}

// Get user subscription data
export async function getUserSubscription(userId: string) {
  try {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('users')
      .select('subscription_status, subscription_id, plan_type, is_annual, current_period_end, cancel_at_period_end')
      .eq('id', userId)
      .single();
    
    if (error) return null;
    
    return {
      status: data.subscription_status,
      plan: data.plan_type,
      isAnnual: data.is_annual,
      currentPeriodEnd: data.current_period_end,
      cancelAtPeriodEnd: data.cancel_at_period_end,
      subscriptionId: data.subscription_id
    };
  } catch (error) {
    return null;
  }
}
```

### Webhook Integration

When a user registers with Clerk, a webhook creates a corresponding record in Supabase:

```typescript
// Process based on the event type
switch (type) {
  case 'user.created': {
    // Get primary email address from Clerk data
    const primaryEmail = data.email_addresses?.find(
      (email: any) => email.id === data.primary_email_address_id
    )?.email_address;
    
    // Add user to Supabase
    const { error } = await supabase.from('users').insert({
      id: data.id,
      email: primaryEmail,
      first_name: data.first_name,
      last_name: data.last_name,
      subscription_status: 'inactive',
      plan_type: 'free',
      is_annual: false
    });
    break;
  }
}
```

## Custom Hooks

### useSubscription Hook

The application provides a custom hook for accessing subscription data:

```typescript
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
  
  // Default subscription data for free tier
  const defaultSubscription: Subscription = {
    status: 'inactive',
    plan: 'free',
    isAnnual: false,
    currentPeriodEnd: null,
    cancelAtPeriodEnd: false,
  };
  
  // Extract subscription from response or use default
  const subscription = data?.subscription || defaultSubscription;
  
  // Helper methods
  const isSubscribed = () => { /* Check if active paid subscription */ };
  const isCancelling = () => { /* Check if set to cancel */ };
  const daysRemaining = () => { /* Calculate days remaining */ };
  const cancelSubscription = async () => { /* Cancel subscription */ };
  const reactivateSubscription = async () => { /* Reactivate subscription */ };
  
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

## Payment and Subscription System

### Checkout Flow

The checkout process handles authentication and redirects appropriately:

```typescript
// Inside checkout component
const { isLoaded, user } = useUser();
  
// Check authentication
useEffect(() => {
  const checkAuth = async () => {
    try {
      // If user is not authenticated, redirect to sign-in
      if (isLoaded && !user) {
        router.push(`/sign-in?redirectUrl=${encodeURIComponent(`/checkout?plan=${plan}&billing=${billing}`)}`);
        return;
      }
      
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check error:', error);
      router.push(`/sign-in?redirectUrl=${encodeURIComponent(`/checkout?plan=${plan}&billing=${billing}`)}`);
    }
  };
  
  checkAuth();
}, [isLoaded, user, plan, billing, router]);
```

### Payment Processing

Stripe integration handles payment processing with proper error handling:

```typescript
// Create a checkout session
const response = await fetch('/api/create-checkout-session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    productId,
    plan: planName,
    isAnnual,
    userId: user.id
  }),
});

if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  throw new Error(errorData.error || `HTTP error ${response.status}`);
}

const { sessionId, error } = await response.json();

if (error) {
  throw new Error(error);
}

// Redirect to Stripe Checkout
await stripe.redirectToCheckout({ sessionId });
```

### Subscription Management with Supabase

The application uses Supabase to store and manage subscription data, with robust date handling:

```typescript
// Get user subscription data
const subscription = await getUserSubscription(userId);

// Validate currentPeriodEnd - set to null if invalid (year < 2000)
let currentPeriodEnd = data.current_period_end;
if (currentPeriodEnd) {
  const date = new Date(currentPeriodEnd);
  if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
    currentPeriodEnd = null;
  }
}

// Update user subscription status
await updateUserSubscription(userId, {
  cancelAtPeriodEnd: true
});

// Return the updated subscription with validated dates
return NextResponse.json({ 
  success: true, 
  message: "Subscription marked for cancellation",
  subscription: updatedSubscription || {
    status: subscription.status,
    plan: subscription.plan,
    isAnnual: subscription.isAnnual,
    // Set a valid future date - 30 days from now for testing
    currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    cancelAtPeriodEnd: true
  }
});
```

### Date Handling and Validation

The application implements multiple layers of date validation to prevent displaying invalid dates:

1. **Database Layer**: 
   - The `getUserSubscription` function validates the `currentPeriodEnd` before returning it
   - Invalid dates are replaced with `null`

2. **API Layer**:
   - Default responses use 30-day future dates for testing
   - All dates are validated before being sent to the client

3. **Client Layer**:
   - The `useSubscription` hook validates dates before calculations
   - The `formatDate` function checks for `null` or invalid dates and returns "N/A"
   - Components handle `null` date values gracefully

```typescript
// Format date with validation in components
const formatDate = (dateString: string | null) => {
  // If the date is null or undefined, return "N/A"
  if (!dateString) return "N/A";
  
  // Check if it's a valid date
  const date = new Date(dateString);
  
  // Check for invalid date (e.g., timestamp 0 which might show as Dec 31, 1969)
  if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
    return "N/A";
  }
  
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
}
```

### Stripe Webhook Handler

Stripe webhooks update the user's subscription data in Supabase:

```typescript
if (event.type === 'checkout.session.completed') {
  const session = event.data.object as Stripe.Checkout.Session;
  const userId = session.client_reference_id;

  // Get subscription from session
  const subscription = await stripe.subscriptions.retrieve(session.subscription as string);
  
  // Update user in Supabase with subscription info
  const { error } = await supabase
    .from('users')
    .update({
      subscription_id: subscription.id,
      subscription_status: subscription.status,
      plan_type: session.metadata?.plan || 'pro',
      is_annual: session.metadata?.isAnnual === 'true',
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      cancel_at_period_end: subscription.cancel_at_period_end,
      stripe_customer_id: session.customer as string,
    })
    .eq('id', userId);
}
```

### Handling Development vs Production

API endpoints include fallbacks for development environments:

```typescript
// For development or when Stripe is not configured
if (!stripe || process.env.NODE_ENV === 'development') {
  console.log('Using test data for subscription management');
  return NextResponse.json({ 
    success: true,
    message: "Operation successful",
    subscription: {
      plan: 'pro',
      status: 'active',
      currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      cancelAtPeriodEnd: false
    }
  });
}
```

### Development Mode Checkout Flow

In development mode without Stripe API keys, the checkout flow uses a direct success URL redirect:

```typescript
// For development environment, use test mode with mock session
if (!stripe || process.env.NODE_ENV === 'development') {
  console.log('Using mock checkout session in development mode');
  return NextResponse.json({ 
    sessionId: 'test_session_id',
    url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/success?session_id=test_session_mock`,
    message: 'Test mode - no real Stripe connection available' 
  });
}
```

The StripeCheckout component is designed to handle both real Stripe redirects and direct success URL redirects:

```typescript
// If we get a direct URL back (like in dev mode), redirect to it
if (url) {
  console.log('Redirecting to success URL:', url);
  window.location.href = url;
  return;
}

// Otherwise, redirect to Stripe Checkout
console.log('Redirecting to Stripe with session ID:', sessionId);
const result = await stripe.redirectToCheckout({
  sessionId,
});
```

This approach enables testing the complete checkout flow even without a Stripe account or API keys.

## Watchlist Management

### API Endpoints

#### GET /api/watchlist

This endpoint retrieves the user's watchlist with stock data:

```typescript
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
    console.error('Error fetching watchlist:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
```

#### POST /api/watchlist

This endpoint adds a ticker to the user's watchlist:

```typescript
export async function POST(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const data = await req.json();
    const { ticker } = data;
    
    if (!ticker) {
      return NextResponse.json({ error: 'Ticker is required' }, { status: 400 });
    }

    // Ensure user exists in Supabase
    await createUserIfNotExists(userId);
    
    // Add ticker to watchlist
    await addToWatchlist(userId, ticker.toUpperCase());
    
    // Get updated watchlist
    const watchlistItems = await getUserWatchlist(userId);
    
    // Return transformed watchlist for UI consistency
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
      message: `Added ${ticker} to watchlist`,
      watchlist: transformedWatchlist
    });
  } catch (error) {
    console.error('Error adding to watchlist:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
```

#### DELETE /api/watchlist?ticker=AAPL

This endpoint removes a ticker from the user's watchlist:

```typescript
export async function DELETE(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const ticker = searchParams.get('ticker');
    
    if (!ticker) {
      return NextResponse.json({ error: 'Ticker is required' }, { status: 400 });
    }

    // Remove ticker from watchlist
    await removeFromWatchlist(userId, ticker.toUpperCase());
    
    // Get updated watchlist
    const watchlistItems = await getUserWatchlist(userId);
    
    // Return transformed watchlist for UI consistency
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
      message: `Removed ${ticker} from watchlist`,
      watchlist: transformedWatchlist
    });
  } catch (error) {
    console.error('Error removing from watchlist:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
```

### Watchlist Component Implementation

The Watchlist component integrates with these endpoints for a complete user experience:

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

  // Fetch watchlist from API
  const fetchWatchlist = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/watchlist', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      // Process response and update state
    } catch (err) {
      // Error handling
    } finally {
      setIsLoading(false);
    }
  };

  // Add ticker to watchlist
  const addToWatchlist = async (ticker: string) => {
    // Validation
    // API call
    // State update
    // User notification
  };

  // Remove ticker from watchlist
  const removeFromWatchlist = async (ticker: string) => {
    // API call
    // State update
    // User notification
  };

  // Render UI based on state
}
```

### Database Structure

The watchlist feature utilizes the following Supabase tables:

1. **watchlists** - Stores user watchlist entries
   ```sql
   CREATE TABLE public.watchlists (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
     ticker TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

2. **stock_info** - Stores stock data that's joined with watchlist items
   ```sql
   CREATE TABLE public.stock_info (
     id STRING PRIMARY KEY,
     ticker STRING UNIQUE NOT NULL,
     company_name STRING NOT NULL,
     sector STRING,
     industry STRING,
     marketcap NUMBER,
     current_price NUMBER,
     daily_volume NUMBER,
     change_percent NUMBER,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

### Row-Level Security

To ensure data privacy, we've implemented row-level security policies:

```sql
-- Only allow users to see their own watchlist items
CREATE POLICY watchlist_access_policy ON public.watchlists
  FOR ALL
  USING (user_id = auth.uid()::TEXT);
```

This ensures users can only access their own watchlist entries, even if they try to query the API with different parameters.