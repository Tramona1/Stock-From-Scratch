import { NextResponse, NextRequest } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import Stripe from 'stripe';
import { getUserSubscription, updateUserSubscription, createUserIfNotExists } from '@/services/users';
import { createClient } from '@/lib/supabase/server';

// Initialize Stripe if the API key is available
const stripe = process.env.STRIPE_SECRET_KEY ? 
  new Stripe(process.env.STRIPE_SECRET_KEY, {
    apiVersion: '2025-02-24.acacia',
  }) : null;

export async function POST(req: NextRequest) {
  try {
    const auth = getAuth(req);
    const userId = auth.userId;
    
    console.log("Auth check in reactivate API - userId:", userId);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // First check if the user exists in the database
    const supabase = createClient();
    
    // Try to create the user if they don't exist yet
    await createUserIfNotExists(userId);
    
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();
      
    if (userError) {
      console.log(`User not found in database for reactivation: ${userId}`, userError);
      return NextResponse.json({ 
        error: 'Cannot reactivate subscription. Your account is not fully set up.',
        code: 'USER_NOT_FOUND'
      }, { status: 404 });
    }
    
    // Get user's subscription
    console.log("Fetching subscription for user:", userId);
    const subscription = await getUserSubscription(userId);
    
    // Can't reactivate if there's no active subscription
    if (!subscription || subscription.status !== 'active') {
      console.log(`No active subscription found for user: ${userId}`);
      return NextResponse.json({ 
        error: 'No active subscription found to reactivate', 
        code: 'NO_ACTIVE_SUBSCRIPTION'
      }, { status: 404 });
    }
    
    // Can't reactivate if it's not set to cancel
    if (!subscription.cancelAtPeriodEnd) {
      console.log(`Subscription is not set to cancel for user: ${userId}`);
      return NextResponse.json({ 
        error: 'Subscription is not set to cancel', 
        code: 'SUBSCRIPTION_NOT_CANCELLING'
      }, { status: 400 });
    }
    
    console.log("Current subscription before reactivation:", JSON.stringify(subscription));
    
    // If no stripe instance or no subscription ID, use mock data for testing
    if (!stripe || !subscription.subscriptionId) {
      console.log("Using test data for subscription reactivation");
      
      // Update subscription in database directly
      await updateUserSubscription(userId, {
        cancelAtPeriodEnd: false
      });
      
      const updatedSubscription = await getUserSubscription(userId);
      
      return NextResponse.json({ 
        success: true, 
        message: "Subscription reactivated in test mode",
        subscription: updatedSubscription || {
          status: 'active',
          plan: subscription.plan,
          isAnnual: subscription.isAnnual,
          currentPeriodEnd: subscription.currentPeriodEnd || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          cancelAtPeriodEnd: false,
          derivedStatus: 'active'
        }
      });
    }
    
    try {
      // Update the subscription in Stripe
      const updatedStripeSubscription = await stripe.subscriptions.update(
        subscription.subscriptionId,
        { cancel_at_period_end: false }
      );
      
      console.log(`Stripe subscription reactivated: ${subscription.subscriptionId} cancel_at_period_end = ${updatedStripeSubscription.cancel_at_period_end}`);
      
      // Then update our own database
      console.log("Updating subscription in database to set cancelAtPeriodEnd = false");
      await updateUserSubscription(userId, {
        cancelAtPeriodEnd: false
      });
      
      // Get updated subscription data
      const updatedSubscription = await getUserSubscription(userId);
      console.log("Updated subscription after reactivation:", JSON.stringify(updatedSubscription));
      
      // Add derived status
      const derivedStatus = 'active';
      
      return NextResponse.json({ 
        success: true, 
        message: "Subscription successfully reactivated.",
        subscription: updatedSubscription ? {
          ...updatedSubscription,
          derivedStatus
        } : null
      });
    } catch (error) {
      console.error('Error reactivating subscription in Stripe:', error);
      return NextResponse.json({ 
        error: 'Failed to reactivate subscription', 
        details: error 
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error in subscription reactivation:', error);
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error
    }, { status: 500 });
  }
} 