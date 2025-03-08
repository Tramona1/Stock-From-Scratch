"use client"

import React, { Suspense } from 'react'
import { useEffect, useState } from 'react'
import { Header } from "@/components/layout/Header"
import { StripeCheckout } from "@/components/payment/StripeCheckout"
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckIcon } from "lucide-react"
import { useUser } from "@clerk/nextjs"
import { loadStripe } from '@stripe/stripe-js'

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '')

// Product IDs provided
const PRODUCT_IDS = {
  pro: {
    monthly: "prod_Rth1zBwvrmAD4x",
    annual: "prod_Rth44Fw2kvCwYf"
  },
  advanced: {
    monthly: "prod_Rth2mEBixmoy4b",
    annual: "prod_Rth485YX7kJaxe"
  }
}

// Add this at the top of the file
export const dynamic = 'force-dynamic';

// Create loading fallback
function CheckoutLoading() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 py-12">
        <div className="container max-w-3xl">
          <div className="animate-pulse space-y-6">
            <div className="h-10 bg-gray-200 rounded w-1/3"></div>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="h-64 bg-gray-200 rounded col-span-2"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Add this component above the CheckoutContent function
function DirectCheckoutButton({ planId, planName, isAnnual }: { planId: 'pro' | 'advanced', planName: string, isAnnual: boolean }) {
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useUser();
  
  const handleDirectCheckout = async () => {
    if (!user) {
      alert("You must be signed in to complete checkout");
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Get the Stripe instance
      const stripe = await stripePromise;
      
      if (!stripe) {
        throw new Error('Stripe failed to initialize');
      }
      
      // Get the product ID based on plan and billing cycle
      const billingType = isAnnual ? 'annual' : 'monthly';
      const productId = PRODUCT_IDS[planId][billingType];
      
      console.log('Creating checkout session with:', { 
        productId, 
        plan: planName, 
        isAnnual, 
        userId: user.id 
      });
      
      // Create a checkout session
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          productId,
          plan: planName,
          isAnnual,
          userId: user.id,
          useMock: false, // Ensure we're not using mock mode
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error ${response.status}`);
      }
      
      const { sessionId, url, error } = await response.json();
      
      if (error) {
        throw new Error(error);
      }
      
      if (sessionId) {
        console.log('Redirecting to Stripe with session ID:', sessionId);
        const result = await stripe.redirectToCheckout({
          sessionId,
        });
        
        if (result.error) {
          throw new Error(result.error.message);
        }
      } else if (url) {
        // Only as a fallback if no sessionId is provided
        console.log('No sessionId found, using direct URL:', url);
        window.location.href = url;
      } else {
        throw new Error('No session ID or URL returned from checkout API');
      }
    } catch (error) {
      console.error('Error during checkout:', error);
      alert('Something went wrong with the checkout process. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <button
      onClick={handleDirectCheckout}
      disabled={isLoading}
      className="w-full py-2 px-4 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
    >
      {isLoading ? 'Processing...' : 'Complete Payment'}
    </button>
  );
}

// Create a client component that uses useSearchParams
function CheckoutContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const { isLoaded, user } = useUser()
  
  const plan = searchParams.get('plan') || 'pro'
  const billing = searchParams.get('billing') || 'monthly'
  const isAnnual = billing === 'annual'
  
  // Verify authentication
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // First try to get auth from Clerk client-side
        if (!isLoaded || !user) {
          // If clerk is still loading, wait
          if (!isLoaded) return;
          
          // If user is not authenticated, redirect to sign-in
          router.push(`/sign-in?redirectUrl=${encodeURIComponent(`/checkout?plan=${plan}&billing=${billing}`)}`)
          return
        }
        
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Auth check error:', error)
        router.push(`/sign-in?redirectUrl=${encodeURIComponent(`/checkout?plan=${plan}&billing=${billing}`)}`)
      }
    }
    
    checkAuth()
  }, [isLoaded, user, plan, billing, router])

  // Plan details based on the plan parameter
  const planDetails = {
    pro: {
      name: "Pro",
      price: isAnnual ? "$143.90" : "$14.99",
      period: isAnnual ? "year" : "month",
      features: [
        "Everything in Free",
        "Advanced technical analysis",
        "AI-powered stock suggestions",
        "Portfolio performance tracking",
        "Custom alerts and notifications",
        "Priority customer support",
        "Watchlist for up to 100 stocks"
      ]
    },
    advanced: {
      name: "Advanced",
      price: isAnnual ? "$287.90" : "$29.99",
      period: isAnnual ? "year" : "month",
      features: [
        "Everything in Pro",
        "Advanced AI market analysis",
        "Unlimited watchlists",
        "Custom strategy backtesting",
        "API access",
        "White-label options",
        "Dedicated account manager",
        "Custom integrations"
      ]
    }
  }[plan as 'pro' | 'advanced'] || {
    name: "Pro",
    price: isAnnual ? "$143.90" : "$14.99",
    period: isAnnual ? "year" : "month",
    features: [
      "Everything in Free",
      "Advanced technical analysis",
      "AI-powered stock suggestions",
      "Portfolio performance tracking",
      "Custom alerts and notifications",
      "Priority customer support",
      "Watchlist for up to 100 stocks"
    ]
  }

  if (!isAuthenticated) {
    return null; // Don't render anything while redirecting
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 py-12">
        <div className="container max-w-3xl">
          <h1 className="text-3xl font-bold mb-6">Complete your purchase</h1>
          
          <div className="grid gap-8 md:grid-cols-2">
            {/* Order Summary */}
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h2 className="text-xl font-bold mb-4">Order Summary</h2>
              
              <div className="mb-4 pb-4 border-b border-gray-100">
                <h3 className="font-medium">{planDetails.name} Plan</h3>
                <p className="text-muted-foreground">{isAnnual ? 'Annual' : 'Monthly'} billing</p>
              </div>
              
              <div className="flex justify-between mb-6">
                <span className="font-medium">Total</span>
                <span className="text-xl font-bold">{planDetails.price}/{planDetails.period}</span>
              </div>
              
              <div className="rounded-md bg-blue-50 p-4 mb-6">
                <p className="text-sm text-blue-700">
                  You'll be charged immediately and will have access to all {planDetails.name} features.
                  {isAnnual && " Your annual subscription saves you 20% compared to monthly billing."}
                </p>
              </div>
              
              <DirectCheckoutButton
                planId={plan as 'pro' | 'advanced'}
                planName={planDetails.name}
                isAnnual={isAnnual}
              />
            </div>
            
            {/* Plan Features */}
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h2 className="text-xl font-bold mb-4">{planDetails.name} Plan Includes:</h2>
              
              <ul className="space-y-3">
                {planDetails.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <CheckIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Wrap with Suspense in main component
export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoading />}>
      <CheckoutContent />
    </Suspense>
  )
} 