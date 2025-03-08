# Subscription Status Implementation

This document explains how subscription statuses are implemented, displayed, and managed in our application.

## Understanding Subscription States

A subscription can exist in several states:

1. **No Subscription / New User**
   - User has no active subscription record in the database
   - Displayed as "Inactive" with a red X icon
   - UI shows "Subscribe Now" button

2. **Active Subscription**
   - User has an active subscription 
   - `status = "active"` and `cancelAtPeriodEnd = false`
   - Displayed as "Active" with a green checkmark icon
   - UI shows "Cancel Subscription" button

3. **Cancelling Subscription**
   - User has cancelled but subscription is still active until the end of the billing period
   - `status = "active"` and `cancelAtPeriodEnd = true`
   - Displayed as "Active (Cancelling)" with a yellow warning icon
   - A yellow alert banner shows when the subscription will end
   - UI shows "Reactivate Subscription" button

4. **Cancelled Subscription**
   - After the billing period, the status becomes "canceled"
   - `status = "canceled"` (set by Stripe webhook)
   - Displayed as "Inactive" with a red X icon
   - UI shows "Subscribe Now" button

## Implementation Details

### Database Structure

In the database, we track:
- `subscription_status`: The actual Stripe status ("active", "canceled", "incomplete", etc.)
- `cancel_at_period_end`: Boolean flag indicating if the subscription is set to cancel
- Other fields like `current_period_end`, `plan_type`, etc.

### Derived Status

To make UI display more intuitive, we derive a status:

```typescript
// Add derived status for UI that shows "cancelling" when appropriate
let derivedStatus = subscription.status;
if (subscription.status === 'active' && subscription.cancelAtPeriodEnd === true) {
  derivedStatus = 'cancelling';
}
```

This derived status is used in the UI to show a more accurate representation of the subscription state.

### API Error Handling

When APIs can't find users or subscriptions:

1. `GET /api/subscriptions`:
   - For new users (404), returns a default subscription structure with `status: "inactive"`
   - For errors, returns the same default structure rather than error codes

2. `POST /api/subscriptions/cancel`:
   - Returns 404 with descriptive error codes like `USER_NOT_FOUND` or `NO_ACTIVE_SUBSCRIPTION`
   - Frontend should handle these errors gracefully

3. `POST /api/subscriptions/reactivate`:
   - Returns 404 for missing users/subscriptions
   - Returns 400 if subscription is not in a cancellable state

### Client-Side Handling

The client-side code:
1. Shows proper alerts based on subscription status
2. Displays appropriate buttons (Subscribe/Cancel/Reactivate)
3. Uses the `derivedStatus` field to determine UI state
4. Falls back to default inactive subscription when API calls fail

## Common Issues and Solutions

### Issue: UI Shows Active When Not Active

If the UI shows "Active" for a new user:
- Check the API response from `/api/subscriptions`
- Ensure default subscription is properly returned
- Verify the UI is using the returned data correctly

### Issue: Can't Cancel Non-Existent Subscription

If users can't cancel subscriptions:
- Check for errors in the console
- Verify API is returning proper error codes
- Ensure UI displays appropriate messages

### Issue: Subscription Status Not Updating

If subscription status doesn't update after actions:
- Check network responses for errors
- Verify the API is updating both Stripe and the database
- Ensure UI is refreshing data after actions

## Testing Subscription States

To test different subscription states:
1. Create a new user (should show "Inactive")
2. Subscribe with test card (should show "Active")
3. Cancel subscription (should show "Active (Cancelling)")
4. Use Stripe Test Clock to advance time (should show "Inactive" again) 