import { NextResponse, NextRequest } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import Stripe from 'stripe';
import { updateUserSubscription } from '@/services/users';

export const dynamic = 'force-dynamic';

// Initialize Stripe with your secret key if available
const stripe = process.env.STRIPE_SECRET_KEY ? 
  new Stripe(process.env.STRIPE_SECRET_KEY, {
    apiVersion: '2025-02-24.acacia',
  }) : null;

export async function POST(req: NextRequest) {
  try {
    // Get the request body
    const body = await req.json();
    const { productId, priceId, plan, isAnnual, userId, useMock = false } = body;
    
    if ((!productId && !priceId) || !userId) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }
    
    // Get auth context - using the getAuth pattern for API routes
    const auth = getAuth(req);
    const authenticatedUserId = auth.userId;
    
    // Security check: ensure the userId from the request matches the authenticated user
    if (!authenticatedUserId || authenticatedUserId !== userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check if Stripe is initialized and show clear error if not
    if (!stripe) {
      console.error('Stripe is not initialized - missing API key in environment variables');
      return NextResponse.json({ 
        error: 'Stripe is not configured. Please check your environment variables.',
        message: 'STRIPE_SECRET_KEY is missing'
      }, { status: 500 });
    }
    
    // If we have a priceId, use it directly
    // Otherwise, we need to look up the price based on the productId
    let actualPriceId = priceId;
    
    if (!actualPriceId && productId) {
      // In production, look up the price from Stripe
      const prices = await stripe.prices.list({
        product: productId,
        active: true,
        limit: 100,
      });
      
      const matchingPrice = prices.data.find(p => 
        (isAnnual && p.recurring?.interval === 'year') || 
        (!isAnnual && p.recurring?.interval === 'month')
      );
      
      if (!matchingPrice) {
        return NextResponse.json({ error: 'Price not found for product' }, { status: 404 });
      }
      
      actualPriceId = matchingPrice.id;
    }
    
    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      billing_address_collection: 'auto',
      line_items: [
        {
          price: actualPriceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/pricing`,
      client_reference_id: userId,
      metadata: {
        userId,
        plan,
        isAnnual: isAnnual ? 'true' : 'false',
      }
    });
    
    // Update user record with pending subscription info
    await updateUserSubscription(userId, {
      plan: plan,
      isAnnual: isAnnual,
      status: 'pending'
    });
    
    return NextResponse.json({ sessionId: session.id, url: session.url });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    return NextResponse.json({ 
      error: 'Error creating checkout session', 
      message: error instanceof Error ? error.message : 'Unknown error' 
    }, { status: 500 });
  }
} 