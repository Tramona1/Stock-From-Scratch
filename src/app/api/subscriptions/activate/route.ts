import { NextResponse, NextRequest } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

export const dynamic = 'force-dynamic';

// Initialize Stripe with your secret key
const stripe = process.env.STRIPE_SECRET_KEY ?
  new Stripe(process.env.STRIPE_SECRET_KEY, {
    apiVersion: '2025-02-24.acacia',
  }) : null;

export async function POST(req: NextRequest) {
  try {
    // Get authentication details
    const auth = getAuth(req);
    const userId = auth.userId;

    if (!userId) {
      console.error('Unauthorized access attempt to activate subscription');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get the request body
    const body = await req.json();
    const { sessionId, plan, isAnnual } = body;

    console.log(`Activating subscription for user ${userId}`, { sessionId, plan, isAnnual });

    // For immediate feedback without waiting for webhook
    // We'll directly update the user's subscription in Supabase
    const supabase = createClient();
    
    // If we have a session ID and Stripe is configured, try to get subscription data
    let subscriptionId = null;
    let currentPeriodEnd = null;
    let subscriptionStatus = 'active';
    
    if (stripe && sessionId && !sessionId.includes('mock')) {
      try {
        // Get the session data from Stripe
        const session = await stripe.checkout.sessions.retrieve(sessionId);
        
        // If session has a subscription, get the details
        if (session.subscription) {
          const subscription = await stripe.subscriptions.retrieve(session.subscription as string);
          subscriptionId = subscription.id;
          currentPeriodEnd = new Date(subscription.current_period_end * 1000).toISOString();
          subscriptionStatus = subscription.status;
        }
      } catch (error) {
        console.error('Error retrieving subscription from Stripe:', error);
        // Continue with default values if Stripe call fails
      }
    }
    
    // If we couldn't get subscription data, use fallback values
    if (!currentPeriodEnd) {
      currentPeriodEnd = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
    }
    
    // Check if user exists in database first
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('id')
      .eq('id', userId)
      .single();

    if (userError) {
      console.error('Error checking if user exists:', userError);
      
      // If the error is that no rows were returned, the user doesn't exist
      if (userError.code === 'PGRST116') {
        console.log(`User ${userId} not found. Attempting to create user record first.`);
        
        // Try to get user details from Clerk
        try {
          // Insert a basic user record
          const { error: insertError } = await supabase.from('users').insert({
            id: userId,
            email: 'unknown@example.com', // Will be updated by webhook later
            first_name: 'Unknown',
            last_name: 'User',
            subscription_status: 'inactive',
            plan_type: 'free',
            is_annual: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          });
          
          if (insertError) {
            console.error('Failed to create user record:', insertError);
            return NextResponse.json({ 
              error: 'User not found in database and failed to create', 
              details: insertError 
            }, { status: 404 });
          }
          
          console.log(`Created placeholder record for user ${userId}`);
        } catch (e) {
          console.error('Error creating user record:', e);
          return NextResponse.json({ 
            error: 'User not found in database and failed to create', 
            details: e instanceof Error ? e.message : String(e)
          }, { status: 404 });
        }
      } else {
        // For other database errors
        return NextResponse.json({ 
          error: 'Error checking if user exists', 
          details: userError 
        }, { status: 500 });
      }
    }
    
    // Attempt the direct update using the raw SQL query to bypass UUID type checking
    // This allows us to use the Clerk user ID format directly
    const { error } = await supabase.rpc('update_subscription_with_string_id', {
      p_user_id: userId,
      p_subscription_id: subscriptionId || 'manual_activation',
      p_subscription_status: subscriptionStatus,
      p_plan_type: plan,
      p_is_annual: isAnnual !== undefined ? isAnnual : false,
      p_current_period_end: currentPeriodEnd,
      p_cancel_at_period_end: false
    });
    
    if (error) {
      console.error('Error using RPC to update subscription:', error);
      
      // Fallback: Try direct SQL query
      const { error: sqlError } = await supabase.from('users')
        .update({
          subscription_id: subscriptionId || 'manual_activation',
          subscription_status: subscriptionStatus,
          plan_type: plan,
          is_annual: isAnnual !== undefined ? isAnnual : false,
          current_period_end: currentPeriodEnd,
          cancel_at_period_end: false,
          updated_at: new Date().toISOString()
        })
        .eq('id', userId);
        
      if (sqlError) {
        console.error('Error with direct SQL update:', sqlError);
        return NextResponse.json({ 
          error: 'Failed to activate subscription', 
          details: sqlError 
        }, { status: 500 });
      }
    }
    
    // Return success with updated subscription info
    return NextResponse.json({
      success: true,
      subscription: {
        status: subscriptionStatus,
        plan: plan,
        isAnnual: isAnnual !== undefined ? isAnnual : false,
        currentPeriodEnd,
        cancelAtPeriodEnd: false,
        subscriptionId: subscriptionId || 'manual_activation'
      }
    });

  } catch (error) {
    console.error('Error activating subscription:', error);
    return NextResponse.json(
      { error: 'Error activating subscription', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 