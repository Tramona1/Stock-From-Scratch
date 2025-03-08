# Supabase Functions

This document outlines the SQL functions created to handle the user ID incompatibility between Clerk and Supabase.

## Problem: UUID vs String ID Incompatibility

Our system encountered an issue with the integration between Clerk and Supabase:

- Clerk generates user IDs in a string format like `user_2tjSfDuQApmcxwHRHszCtKZpKGs`
- Supabase's `users` table was initially configured with an `id` column of type UUID
- When attempting to query or update users with Clerk IDs, Postgres failed to cast the string to UUID

This resulted in errors like:

```
Error updating user subscription: {
  code: '22P02',
  details: null,
  hint: null,
  message: 'invalid input syntax for type uuid: "user_2tjSfDuQApmcxwHRHszCtKZpKGs"'
}
```

## Temporary Solution: SQL Functions with Type Casting

We initially created the following SQL functions to bypass Postgres's type checking by explicitly casting IDs to TEXT:

### 1. Update Subscription Function

```sql
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
```

### 2. Get Subscription Function

```sql
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

## Permanent Solution: Database Schema Update

Instead of relying on functions with type casting, we implemented a more direct solution by changing the database schema itself:

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

This schema change allows Clerk's string-formatted user IDs to be stored directly in Supabase without any type conversion or special handling, eliminating the need for the custom SQL functions.

## Implementation Notes

### When to Use SQL Functions vs Schema Changes

- **SQL Functions**: A good temporary solution when you cannot immediately modify the database schema
- **Schema Changes**: The preferred long-term solution, as it eliminates the need for special handling

### Migration Path

When implementing the schema change:

1. First take a database backup
2. Drop any RLS policies that reference the ID column
3. Alter the column type from UUID to TEXT
4. Recreate the RLS policies with TEXT comparison
5. Update any API code that makes assumptions about ID format

### Impact on Existing Records

- If you have existing records with UUID values, they will be preserved as text representations
- All new user records will store Clerk's string IDs directly

### Security Considerations

When modifying RLS policies, ensure that:

1. The `auth.uid()` value is properly cast to TEXT (e.g., `id = auth.uid()::TEXT`)
2. All security tests are re-run to verify policy enforcement
3. Foreign key constraints are updated if necessary

## API Usage

After implementing the schema change, the special SQL functions are no longer needed. API code can directly use:

```typescript
// Update user subscription
const { error } = await supabase
  .from('users')
  .update({
    subscription_status: 'active',
    // other fields...
  })
  .eq('id', userId);

// Get user subscription
const { data, error } = await supabase
  .from('users')
  .select('subscription_status, subscription_id, plan_type, is_annual, current_period_end, cancel_at_period_end')
  .eq('id', userId)
  .single();
```

The Supabase client API will automatically handle the TEXT format of user IDs without requiring any special functions or type casting.

## Conclusion

Changing the `id` column type from UUID to TEXT is the most direct solution to the Clerk-Supabase integration issue. While the SQL functions provide a temporary workaround, modifying the schema is recommended for a clean, maintenance-free solution. 