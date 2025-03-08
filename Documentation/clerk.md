RULES FOR DOCUEMNTATION: DO NOT REMOVE!!; Make sure you are adding very in-depth descriptions everywhere from every single file that's involved to how it's working. This will be used to discuss with our CTO, so make sure that every single thing they could ever need is documented in here with the changes as you are making them

1. Added ClerkProvider to the root layout
2. Created login and signup pages
3. Set up middleware for route protection
4. Created auth guard component for client-side protection
5. Updated Header to show login/signup links or user menu
6. Created UserMenu component
7. Added API routes for user data
8. Created SQL for Supabase users table
9. Added webhook route for Clerk events
10. Added useAuth hook
11. Updated dashboard layout to use AuthGuard
12. Added SSO callback pages to properly handle authentication redirects

I'll structure the documentation to show:
1. What we've accomplished
2. What each file does
3. The overall authentication flow
4. Next steps or considerations

# Authentication Implementation Documentation

## Overview

We have implemented a comprehensive authentication system using Clerk, integrated with Supabase for data storage and Stripe for subscription management. This architecture provides a secure, scalable, and feature-rich authentication solution.

## Key Components Implemented

### 1. Authentication Configuration

| File | Purpose |
|------|---------|
| `middleware.ts` | Protects routes at the application level using Clerk's authMiddleware |
| `src/app/layout.tsx` | Added ClerkProvider to wrap the entire application |

### 2. Authentication Pages

| File | Purpose |
|------|---------|
| `src/app/auth/login/[[...sign-in]]/page.tsx` | Displays Clerk's SignIn component with custom styling |
| `src/app/auth/signup/[[...sign-up]]/page.tsx` | Displays Clerk's SignUp component with custom styling |

### 3. Protected Routes and Components

| File | Purpose |
|------|---------|
| `src/components/auth/AuthGuard.tsx` | Client-side guard component that redirects unauthenticated users |
| `src/app/dashboard/layout.tsx` | Updated to use AuthGuard for protecting all dashboard routes |

### 4. User Interface Components

| File | Purpose |
|------|---------|
| `src/components/auth/UserMenu.tsx` | Displays user avatar and settings button when logged in |
| `src/components/layout/Header.tsx` | Updated to conditionally show login/signup buttons or UserMenu |

### 5. API and Data Layer

| File | Purpose |
|------|---------|
| `src/app/api/auth/user/route.ts` | API endpoints for getting and updating user data |
| `src/app/api/webhooks/clerk/route.ts` | Webhook handler for Clerk events (e.g., user creation) |
| `src/lib/supabase/server.ts` | Server-side Supabase client for database operations |
| `src/services/users.ts` | User service layer for accessing and updating user data |
| `users_table_migration.sql` | SQL for creating the users table in Supabase |

### 6. Utilities and Hooks

| File | Purpose |
|------|---------|
| `src/hooks/useAuth.ts` | Custom hook for accessing authentication state and user data |
| `src/hooks/useSubscription.ts` | Custom hook for accessing and managing subscription data |
| `src/app/dashboard/settings/page.tsx` | Updated to use Clerk user data and API |

## Authentication Flow

1. **User Registration**:
   - User signs up via `/auth/signup`
   - Clerk handles auth and creates the user
   - Webhook triggers creation of Supabase user record with default values

2. **User Login**:
   - User logs in via `/auth/login`
   - Clerk authenticates and establishes session
   - JWT is used for subsequent API requests
   - Client-side components get auth state using the `useUser` hook

3. **Protected Resources**:
   - Routes are protected via middleware
   - Dashboard is further protected via AuthGuard
   - API endpoints verify authentication via Clerk's getAuth
   - Server-side API routes use getAuth + Supabase client to get/update data

4. **User Data Access**:
   - User profile combines data from Clerk and Supabase
   - Settings page allows updating both sources
   - useAuth hook provides easy access to auth state and user data

## Data Integration Pattern

The application uses a robust pattern for integrating Clerk with Supabase:

1. **Initialization**:
   - Clerk is the source of truth for authentication state
   - Clerk webhooks initialize Supabase user records
   - Supabase stores extended user data including subscription info

2. **Data Synchronization**:
   - Webhooks ensure data consistency between systems
   - User updates from Clerk propagate to Supabase
   - Subscription updates from Stripe also update Supabase

3. **Data Access**:
   - Client components access auth state through Clerk hooks
   - API endpoints authenticate with Clerk, then access Supabase data
   - Type-safe database interactions with TypeScript interfaces

## Payment Integration with Authentication

1. **Checkout Flow**:
   - Payment pages check authentication status with Clerk
   - Unauthenticated users are redirected to sign-in with return URL
   - After authentication, users are returned to checkout flow
   - Parameter `redirectUrl` is used to maintain consistency

2. **Subscription Management**:
   - API routes verify user identity through Clerk before any subscription changes
   - User ID from authentication is compared with requested user ID
   - Development fallbacks provide testing capabilities without real payment
   - Supabase stores subscription details for quick access

3. **Error Handling**:
   - Authentication failures redirect to sign-in
   - Payment processing errors provide user-friendly messages
   - API responses include detailed error information for troubleshooting

## Security Features

1. **Route Protection**: All dashboard and API routes are protected by Clerk
2. **API Authentication**: All user data requests require valid JWT
3. **Webhook Verification**: Clerk webhooks are cryptographically verified
4. **Database Security**: Row-level security in Supabase ensures users only access their data
5. **Type Safety**: TypeScript interfaces ensure correct data handling

## Routing Structure

To avoid routing conflicts, we use the following structure:
- `/auth/login/[[...sign-in]]/page.tsx` (catch-all route)
- `/auth/signup/[[...sign-up]]/page.tsx` (catch-all route)

This prevents conflicts with the direct routes and ensures proper handling of Clerk's authentication flow.

## Best Practices

1. **Consistent Redirect Parameters**:
   - Use `redirectUrl` consistently across the application
   - Encode the URL to prevent issues with special characters

2. **Authentication State Management**:
   - Use Clerk's `useUser()` hook for client-side auth state
   - Use `getAuth()` for server components and API routes

3. **Error Handling**:
   - Always include clear error messages in API responses
   - Handle loading states to prevent premature redirects

4. **Development vs Production**:
   - Include fallbacks for when external services are unavailable
   - Use environment variables to control behavior

## Setup and Configuration

### Environment Variables

Add these environment variables to your `.env.local` file:

```
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_XXXXX
CLERK_SECRET_KEY=sk_test_XXXXX
CLERK_WEBHOOK_SECRET=whsec_XXXXX

# Clerk URLs
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxxx
```

### Key Components and Files

#### API Routes
- `src/app/api/auth/user/route.ts` - Handles user profile data
- `src/app/api/webhooks/clerk/route.ts` - Processes Clerk webhooks

#### User Interface
- `src/components/layout/Header.tsx` - Contains profile dropdown with user actions
- `src/app/auth/login/[[...sign-in]]/page.tsx` - User login page
- `src/app/auth/signup/[[...sign-up]]/page.tsx` - User registration page

#### Database Integration
- `src/services/users.ts` - Functions for user data access
- `src/hooks/useSubscription.ts` - Hook for subscription management

## Database Integration

Users data is synchronized between Clerk and Supabase:
1. Clerk handles authentication and stores core user data
2. When a user is created in Clerk, a webhook creates a corresponding record in Supabase
3. Supabase stores additional user metadata including subscription status

## Database Schema

```sql
CREATE TABLE public.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  first_name TEXT,
  last_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  subscription_status TEXT DEFAULT 'inactive',
  subscription_id TEXT,
  stripe_customer_id TEXT,
  plan_type TEXT DEFAULT 'free',
  is_annual BOOLEAN DEFAULT false,
  current_period_end TIMESTAMP WITH TIME ZONE,
  cancel_at_period_end BOOLEAN DEFAULT false,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add row-level security policy
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Only allow users to see their own data
CREATE POLICY user_access_own_data ON public.users
  FOR ALL
  USING (id = auth.uid());
```

# Clerk Integration

RULES FOR DOCUEMNTATION: DO NOT REMOVE!!; Make sure you are adding very in-depth descriptions everywhere from every single file that's involved to how it's working. This will be used to discuss with our CTO, so make sure that every single thing they could ever need is documented in here with the changes as you are making them

## Recent Improvements: Webhook and User ID Integration

### User ID Format Compatibility

We resolved a critical issue with Clerk and Supabase integration related to user ID format:

1. **Problem Identified**: Clerk generates user IDs in a string format (e.g., `user_2tjSfDuQApmcxwHRHszCtKZpKGs`), but our Supabase database was configured with a UUID column type for the `users.id` field.

2. **Database Schema Update**: We modified the database to properly support Clerk's user ID format:
   ```sql
   -- Drop existing policies first
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
   
   CREATE POLICY user_update_own ON public.users
     FOR UPDATE
     USING (id = auth.uid()::TEXT);
   ```

3. **Enhanced Webhook Implementation**: We improved the webhook that creates users in Supabase when they sign up through Clerk. The webhook now:
   - Validates if a user already exists before attempting to create a duplicate
   - Properly extracts the primary email address
   - Includes enhanced error handling and logging
   - Creates the user with their original Clerk ID in the proper format

### Improved Webhook Code

The updated webhook implementation in `src/app/api/webhooks/clerk/route.ts`:

```typescript
export async function POST(request: Request) {
  // Webhook verification logic...
  
  const event = await request.json();
  const { type, data } = event;
  
  try {
    switch (type) {
      case 'user.created': {
        console.log(`Creating Supabase user record for user ${data.id}`);
        
        // Check if the user already exists in Supabase (prevent duplicates)
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
        
        // Extract primary email
        const primaryEmail = data.email_addresses?.find(
          (email: any) => email.id === data.primary_email_address_id
        )?.email_address;
        
        if (!primaryEmail) {
          console.error('No primary email found for user:', data.id);
          return NextResponse.json({ error: 'No primary email found' }, { status: 400 });
        }
        
        // Add user to Supabase with the string ID
        const userData = {
          id: data.id, // Clerk string ID now works directly with TEXT column
          email: primaryEmail,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          subscription_status: 'inactive',
          plan_type: 'free',
          is_annual: false,
          created_at: new Date(),
          updated_at: new Date()
        };

        console.log('Inserting user into Supabase:', userData);
        
        const { error } = await supabase.from('users').insert(userData);
        
        if (error) {
          console.error('Error creating user in Supabase:', error);
          return NextResponse.json({ error: 'Failed to create user in Supabase' }, { status: 500 });
        }
        
        console.log(`Successfully created user ${data.id} in Supabase`);
        return NextResponse.json({ success: true });
      }
      
      // Handle other webhook events...
    }
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### Fallback User Creation

For robustness, we also implemented a fallback user creation mechanism in the subscription activation flow. This ensures that even if the webhook fails or a user record is missing for any reason, we can still create it on-demand:

```typescript
// src/app/api/subscriptions/activate/route.ts
// Check if user exists in database first
const { data: user, error: userError } = await supabase
  .from('users')
  .select('id, email')
  .eq('id', userId)
  .single();

if (userError) {
  if (userError.code === 'PGRST116') {
    // User not found, create placeholder record
    console.log(`User ${userId} not found in database, creating placeholder record`);
    
    // Get user info from Clerk
    const userSession = await clerkClient.users.getUser(userId);
    const primaryEmailObj = userSession.emailAddresses.find(
      email => email.id === userSession.primaryEmailAddressId
    );
    
    // Create user record
    const userData = {
      id: userId,
      email: primaryEmailObj?.emailAddress || 'unknown@example.com',
      first_name: userSession.firstName || '',
      last_name: userSession.lastName || '',
      subscription_status: 'inactive',
      plan_type: 'free',
      is_annual: false,
      created_at: new Date(),
      updated_at: new Date()
    };
    
    const { error: createError } = await supabase.from('users').insert(userData);
    
    if (createError) {
      console.error('Error creating user record:', createError);
      return NextResponse.json(
        { error: 'Failed to create user record' },
        { status: 500 }
      );
    }
    
    console.log(`Created placeholder user record for ${userId}`);
  } else {
    console.error('Error checking for user:', userError);
  }
}
```

## SSO Callback and Routing Improvements

### Problem Identified

We discovered a critical issue with our authentication flow:

1. When users completed the sign-up process, they were redirected to a white screen at `/sign-up/sso-callback` instead of being properly sent to the dashboard.
2. The navigation UI still showed "Sign In" and "Sign Up" buttons even after successful authentication.

The root causes were:
- Missing middleware configuration to allow SSO callback routes
- Missing or improperly configured route handlers for Clerk's callback paths
- Routing conflicts between standard and catch-all routes

### Solution Implemented

We made several improvements to fix these issues:

#### 1. Enhanced Middleware Configuration

Updated `middleware.ts` to properly handle authentication routes:

```typescript
// Updated public routes array in middleware.ts
const publicRoutes = [
  "/", 
  "/auth/login", 
  "/auth/signup", 
  "/api/public(.*)",
  "/sign-in", 
  "/sign-up",
  "/sign-in/sso-callback(.*)",
  "/sign-up/sso-callback(.*)",
  "/pricing"
];

// Updated redirect logic
if (!userId) {
  return NextResponse.redirect(new URL('/sign-in', req.url));
}
```

This ensures:
- SSO callback routes are publicly accessible
- Main sign-in/sign-up routes are accessible
- Unauthorized users are redirected to the correct sign-in page

#### 2. Proper Route Handler Configuration

Fixed the sign-in and sign-up pages to correctly handle Clerk's routing:

```typescript
// src/app/sign-in/page.tsx and src/app/sign-up/page.tsx
<SignIn 
  appearance={{
    elements: {
      rootBox: "mx-auto",
      card: "shadow-none",
    }
  }}
  routing="path"
  path="/sign-in"
  signUpUrl="/sign-up"
  redirectUrl={redirectUrl}
/>
```

Key configuration properties:
- `routing="path"` - Tells Clerk to use path-based routing
- `path="/sign-in"` - Specifies the base path for sign-in
- `redirectUrl={redirectUrl}` - Preserves any redirect URL from query parameters

#### 3. Resolved Routing Conflicts

Next.js has a routing conflict when there are both:
- A regular page route (e.g., `/sign-in/page.tsx`)
- A catch-all route at the same path (e.g., `/sign-in/[[...sign-in]]/page.tsx`)

We fixed this by:
- Removing redundant catch-all routes
- Properly configuring the main sign-in and sign-up pages
- Using dynamic redirects to preserve the intended flow

#### 4. Improved Error Handling and Loading States

Added proper loading states and error handling for the authentication process:

```typescript
// Loading component for sign-up and sign-in pages
function SignUpLoading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse space-y-4 bg-white p-8 rounded-lg border w-full max-w-md">
        <div className="h-10 bg-gray-200 rounded w-1/2 mx-auto"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded w-1/2 mx-auto"></div>
      </div>
    </div>
  )
}

// Suspense wrapper for handling loading state
export default function SignUpPage() {
  return (
    <Suspense fallback={<SignUpLoading />}>
      <SignUpContent />
    </Suspense>
  );
}
```

### Complete Authentication Flow

With these improvements, the authentication flow now works as follows:

1. **User Visits Sign-Up Page**: The user navigates to `/sign-up` and fills out the registration form
2. **Form Submission**: Clerk processes the form and handles account creation
3. **SSO Callback**: Clerk redirects to `/sign-up/sso-callback?after_sign_up_url=/dashboard`
4. **Seamless Handling**: Our middleware allows this callback route without interruption
5. **Successful Redirect**: The user is redirected to the dashboard after successful authentication
6. **Updated UI**: The header shows the user menu instead of sign-in/sign-up buttons

### Key Files Updated

1. **Middleware Configuration**: `middleware.ts`
   - Updated public routes array to include SSO callback paths
   - Changed redirect to use `/sign-in` instead of `/auth/login`

2. **Authentication Pages**:
   - `src/app/sign-in/page.tsx` - Updated with correct Clerk configuration
   - `src/app/sign-up/page.tsx` - Added `routing="path"` property and improved redirects

3. **Route Structure**:
   - Removed redundant catch-all routes that caused conflicts
   - Ensured proper handling of query parameters for redirects

## End-to-End User Creation Flow

With these improvements, our user creation and authentication flow now works seamlessly:

1. **User Signs Up**: User creates an account through Clerk
2. **Webhook Triggered**: Clerk sends a webhook event to our application
3. **User Record Created**: Our webhook handler creates a user record in Supabase with the Clerk ID
4. **Fallback Mechanism**: If the webhook fails, user records are created on-demand when needed
5. **Consistent ID Format**: All operations use the same TEXT format for user IDs

This revised approach ensures that:
- User records are properly created in Supabase
- Subscriptions and other user data can be correctly associated with Clerk user accounts
- The application is resilient to potential webhook failures
- All database operations work correctly with Clerk's string-formatted user IDs

## User Authentication Flow

Our authentication flow is handled by Clerk with middleware integration. The updated flow:

1. **Client-Side Authentication**: Handled by Clerk components
2. **Server-Side Checks**: Using the `auth()` function from the Clerk SDK
3. **Database Operations**: Using the user ID from Clerk directly with Supabase
4. **RLS Policies**: Updated to compare TEXT IDs with `auth.uid()::TEXT`

Example of the updated server-side authentication check:

```typescript
export async function GET() {
  const { userId } = auth();
  
  if (!userId) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }
  
  // Now userId can be used directly with Supabase queries
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .eq('id', userId)
    .single();
  
  // Rest of the function...
}
```

## SSO Callback Implementation

We've implemented dedicated pages to handle SSO (Single Sign-On) callbacks from Clerk. These pages are critical for properly completing the authentication flow when users sign in or sign up through third-party providers or email magic links.

### SSO Callback Pages

1. **Sign-Up SSO Callback**: `/sign-up/sso-callback/page.tsx`
   - Handles callbacks during the sign-up process
   - Properly processes authentication state
   - Displays loading UI while authentication completes
   - Redirects to the dashboard or appropriate page

2. **Sign-In SSO Callback**: `/sign-in/sso-callback/page.tsx`
   - Similar implementation for the sign-in flow
   - Ensures users are properly authenticated
   - Handles errors gracefully

### Implementation Details

Both pages use Clerk's `handleRedirectCallback` function to process the authentication state:

```typescript
const result = await handleRedirectCallback({
  redirectUrl: window.location.href,
  afterSignInUrl: "/dashboard",
  afterSignUpUrl: "/dashboard",
});
```

The pages also handle URL parameters, allowing custom redirect URLs to be specified:

```typescript
const afterSignInUrl = searchParams.get("after_sign_in_url") || "/dashboard"
const afterSignUpUrl = searchParams.get("after_sign_up_url") || "/dashboard"
```

### Middleware Configuration

The SSO callback routes are configured as public routes in the middleware:

```typescript
const publicRoutes = [
  // Other public routes...
  "/sign-in/sso-callback(.*)",
  "/sign-up/sso-callback(.*)",
];
```

This ensures that users can complete the authentication process without being redirected back to the login page.

### Common Issues

If users experience blank screens during authentication:
1. Check browser console for errors
2. Verify that the SSO callback pages are correctly implemented
3. Ensure the middleware allows access to the callback routes
4. Check that the Clerk configuration in the environment variables is correct

By implementing these dedicated callback pages, we've ensured a smooth authentication experience, preventing blank screens or broken flows during the sign-in and sign-up processes.

### SSO Callback Handling

We've implemented dedicated pages for handling SSO (Single Sign-On) callback redirects:

- `/sign-up/sso-callback/page.tsx`: Handles redirects during the sign-up process with SSO providers
- `/sign-in/sso-callback/page.tsx`: Handles redirects during the sign-in process with SSO providers

These pages solve an issue where users would see a blank screen or an intermediate "fill in missing fields" form during SSO authentication. The implementation:

1. Creates a user-friendly loading screen while authentication completes
2. Uses Clerk's `handleRedirectCallback` function to process the authentication
3. Adds proper error handling and logging
4. Explicitly routes users to the dashboard after successful authentication
5. Uses the `skipFirstFactorUrl` option to bypass unnecessary profile completion screens
6. Provides detailed console logs for debugging

Key implementation details:
```tsx
// Process the callback with options to skip unnecessary screens
const options = {
  redirectUrl,
  afterSignInUrl,
  afterSignUpUrl,
  skipFirstFactorUrl: true // This prevents the "fill in missing fields" form
}

const result = await handleRedirectCallback(options)

// Handle different response statuses
if (result.status === "complete") {
  router.push(afterSignInUrl)
} else if (result.firstFactorVerification?.status === "transferable") {
  router.push(afterSignInUrl)
}
```

### Middleware Configuration

The middleware is configured to allow these callback routes as public paths:

```typescript
const publicRoutes = [
  // ...other public routes
  "/sign-in/sso-callback(.*)",
  "/sign-up/sso-callback(.*)",
];
```

### ClerkProvider Configuration

The main layout configures `ClerkProvider` with appearance settings:

```tsx
<ClerkProvider
  appearance={{
    variables: {
      colorPrimary: 'hsl(var(--primary))',
    }
  }}
>
  {/* App content */}
</ClerkProvider>
```

### Sign-Up Page Configuration

The sign-up page uses Clerk's `SignUp` component with custom styling and configuration:

```tsx
<SignUp 
  appearance={{
    elements: {
      rootBox: "mx-auto",
      card: "shadow-none",
      formFieldInput: "rounded-md border-gray-300 focus:border-primary focus:ring-primary",
      formButtonPrimary: "bg-primary hover:bg-primary/90",
      socialButtonsBlockButton: "border border-gray-300 hover:bg-gray-50",
      footer: "text-center text-xs text-gray-500"
    },
    variables: {
      colorPrimary: 'hsl(var(--primary))',
      colorText: 'hsl(var(--foreground))',
      colorBackground: 'white',
      spacingUnit: '4px',
      borderRadius: '8px'
    }
  }}
  routing="path"
  path="/sign-up"
  signInUrl="/sign-in"
  redirectUrl={redirectUrl}
  afterSignUpUrl={redirectUrl}
/>
```

## Debugging SSO Issues

If you encounter SSO authentication issues:

1. Check the browser console for detailed logs from the SSO callback pages
2. Verify that the middleware correctly allows the SSO callback routes
3. Ensure the Clerk application settings match our environment variables
4. Check that `redirectUrl` is being passed correctly to `handleRedirectCallback`
5. Verify network requests to ensure the Clerk API is responding as expected

## Clerk Dashboard Configuration

For the smoothest user experience, configure the following in the Clerk Dashboard:

1. Under "User & Authentication" → "Email, Phone, Username":
   - Set "Name" requirements to "Optional" 
   - Uncheck "Collect first and last names in sign-up"

2. Under "Social Connections":
   - Enable desired providers (Google, GitHub, etc.)
   - Configure redirect URLs to include:
     - `https://yourdomain.com/sign-in/sso-callback`
     - `https://yourdomain.com/sign-up/sso-callback`
