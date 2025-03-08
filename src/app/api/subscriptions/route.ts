import { NextRequest, NextResponse } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import { getUserSubscription, createUserIfNotExists } from '@/services/users';
import { createClient } from '@/lib/supabase/server';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    console.log(`API: Fetching subscription for user: ${userId}`);
    
    // Check if user exists in database first
    const supabase = createClient();
    let subscription = null;
    
    try {
      // Try to get the Clerk user info for email
      const clerkResponse = await fetch(`https://api.clerk.dev/v1/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${process.env.CLERK_SECRET_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      
      let email = null;
      let firstName = null;
      let lastName = null;
      
      if (clerkResponse.ok) {
        const clerkData = await clerkResponse.json();
        email = clerkData.email_addresses?.[0]?.email_address;
        firstName = clerkData.first_name;
        lastName = clerkData.last_name;
        console.log(`Got Clerk data for user ${userId}: ${email}`);
      } else {
        console.log(`Failed to get Clerk data for user ${userId}`);
      }
      
      // Automatically create the user in Supabase if they don't exist
      const userCreated = await createUserIfNotExists(userId, email, firstName, lastName);
      
      if (userCreated) {
        console.log(`User ${userId} exists or was created in Supabase`);
      } else {
        console.log(`Failed to ensure user ${userId} exists in Supabase`);
      }
      
      const { data: user, error: userError } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single();

      if (userError) {
        console.log(`User not found in database: ${userId}`, userError);
        
        // Return a proper default subscription for new users
        return NextResponse.json({ 
          subscription: {
            status: 'inactive',
            plan: 'free',
            isAnnual: false,
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            subscriptionId: null,
            derivedStatus: 'inactive'
          } 
        });
      }
      
      // User exists, fetch their subscription
      subscription = await getUserSubscription(userId);
      
      if (!subscription) {
        console.log(`No subscription found for existing user: ${userId}`);
        // Return default inactive subscription for existing user with no subscription
        return NextResponse.json({ 
          subscription: {
            status: 'inactive',
            plan: 'free',
            isAnnual: false,
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            subscriptionId: null,
            derivedStatus: 'inactive'
          } 
        });
      }
      
      console.log(`Fetched from getUserSubscription:`, JSON.stringify(subscription));
      console.log(`Returning subscription with cancelAtPeriodEnd: ${subscription.cancelAtPeriodEnd}`);
      
      // Check directly in database for cancel_at_period_end value for debugging
      const { data: directCheck } = await supabase
        .from('users')
        .select('cancel_at_period_end')
        .eq('id', userId)
        .single();
      
      console.log(`Direct DB check - cancel_at_period_end value:`, directCheck?.cancel_at_period_end);
      
      // Add derived status for UI that shows "cancelling" when appropriate
      let derivedStatus = subscription.status;
      if (subscription.status === 'active' && subscription.cancelAtPeriodEnd === true) {
        derivedStatus = 'cancelling';
      }
      
      console.log('Returning subscription with derivedStatus:', derivedStatus);
      
      return NextResponse.json({ 
        subscription: {
          ...subscription,
          derivedStatus
        }
      });
      
    } catch (error) {
      console.error('Error in subscription API:', error);
      // Return default inactive subscription on error
      return NextResponse.json({ 
        subscription: {
          status: 'inactive',
          plan: 'free',
          isAnnual: false,
          currentPeriodEnd: null,
          cancelAtPeriodEnd: false,
          subscriptionId: null,
          derivedStatus: 'inactive'
        } 
      });
    }
  } catch (error) {
    console.error('Unexpected error in subscription API:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error }, 
      { status: 500 }
    );
  }
} 