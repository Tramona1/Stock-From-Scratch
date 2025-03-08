import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-02-24.acacia',
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET || '';

// New way to configure the route without using 'bodyParser: false'
export const dynamic = 'force-dynamic';
export const runtime = 'edge'; // Optional: Use Edge runtime for better performance

export async function POST(req: Request) {
  const body = await req.text();
  const signature = headers().get('stripe-signature')!;

  if (!signature) {
    return NextResponse.json({ error: 'Missing stripe-signature' }, { status: 400 });
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    console.error(`Webhook signature verification failed: ${err}`);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  // Handle the event
  const supabase = createClient();

  try {
    if (event.type === 'checkout.session.completed') {
      const session = event.data.object as Stripe.Checkout.Session;
      const customerId = session.customer as string;
      const subscriptionId = session.subscription as string;
      const userId = session.client_reference_id; // We'll set this in create-checkout-session

      if (!userId) {
        throw new Error('No user ID in session');
      }

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
          stripe_customer_id: customerId,
          updated_at: new Date().toISOString(),
        })
        .eq('id', userId);

      if (error) throw error;
    }

    if (event.type === 'customer.subscription.updated') {
      const updatedSubscription = event.data.object as Stripe.Subscription;
      
      // Find user with this subscription ID
      const { data: users } = await supabase
        .from('users')
        .select('id')
        .eq('subscription_id', updatedSubscription.id);
      
      if (users && users.length > 0) {
        await supabase.from('users').update({
          subscription_status: updatedSubscription.status,
          current_period_end: new Date(updatedSubscription.current_period_end * 1000).toISOString(),
          cancel_at_period_end: updatedSubscription.cancel_at_period_end,
          updated_at: new Date().toISOString(),
        }).eq('subscription_id', updatedSubscription.id);
      }
    }

    if (event.type === 'customer.subscription.deleted') {
      const deletedSubscription = event.data.object as Stripe.Subscription;
      
      // Update user's subscription status
      await supabase.from('users').update({
        subscription_status: 'canceled',
        cancel_at_period_end: false,
        updated_at: new Date().toISOString(),
      }).eq('subscription_id', deletedSubscription.id);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json(
      { error: 'Error processing webhook' },
      { status: 500 }
    );
  }
} 