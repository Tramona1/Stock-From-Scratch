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
    // Get auth using the request object
    const auth = getAuth(req);
    const userId = auth.userId;
    
    console.log("Auth check in cancel API - userId:", userId);
    
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
      console.log(`User not found in database for cancellation: ${userId}`, userError);
      return NextResponse.json({ 
        error: 'Cannot cancel subscription. Your account is not fully set up.',
        code: 'USER_NOT_FOUND'
      }, { status: 404 });
    }
    
    // Get user's subscription
    console.log("Fetching subscription for user:", userId);
    const subscription = await getUserSubscription(userId);
    
    // Can't cancel if there's no active subscription
    if (!subscription || subscription.status !== 'active') {
      console.log(`No active subscription found for user: ${userId}`);
      return NextResponse.json({ 
        error: 'No active subscription found', 
        code: 'NO_ACTIVE_SUBSCRIPTION' 
      }, { status: 404 });
    }
    
    console.log("Current subscription before cancellation:", JSON.stringify(subscription));
    
    // If no stripe instance or no subscription ID, use mock data for testing
    if (!stripe || !subscription.subscriptionId) {
      console.log("Using test data for subscription cancellation");
      
      // Update subscription in database directly
      await updateUserSubscription(userId, {
        cancelAtPeriodEnd: true
      });
      
      const updatedSubscription = await getUserSubscription(userId);
      
      return NextResponse.json({ 
        success: true, 
        message: "Subscription marked for cancellation in test mode",
        subscription: updatedSubscription || {
          status: 'active',
          plan: subscription.plan,
          isAnnual: subscription.isAnnual,
          currentPeriodEnd: subscription.currentPeriodEnd || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          cancelAtPeriodEnd: true,
          derivedStatus: 'cancelling'
        }
      });
    }
    
    try {
      // Update the subscription in Stripe
      const updatedStripeSubscription = await stripe.subscriptions.update(
        subscription.subscriptionId,
        { cancel_at_period_end: true }
      );
      
      console.log(`Stripe subscription updated: ${subscription.subscriptionId} cancel_at_period_end = ${updatedStripeSubscription.cancel_at_period_end}`);
      
      // Then update our own database
      console.log("Updating subscription in database to set cancelAtPeriodEnd = true");
      await updateUserSubscription(userId, {
        cancelAtPeriodEnd: true
      });
      
      // Get updated subscription data
      const updatedSubscription = await getUserSubscription(userId);
      console.log("Updated subscription after cancellation:", JSON.stringify(updatedSubscription));
      
      // Add derived status
      const derivedStatus = 'cancelling';
      
      return NextResponse.json({ 
        success: true, 
        message: "Subscription cancelled. You'll continue to have access until the end of your billing period.",
        subscription: updatedSubscription ? {
          ...updatedSubscription,
          derivedStatus
        } : null
      });
    } catch (error) {
      console.error('Error cancelling subscription in Stripe:', error);
      return NextResponse.json({ 
        error: 'Failed to cancel subscription', 
        details: error 
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error in subscription cancellation:', error);
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error
    }, { status: 500 });
  }
} 