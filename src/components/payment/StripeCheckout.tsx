"use client"

import { useState, useEffect } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Button } from "@/components/ui/button"
import { useRouter } from 'next/navigation'
import { useUser } from '@clerk/nextjs'

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

interface StripeCheckoutProps {
  planId: string
  planName: string
  isAnnual: boolean
  buttonText?: string
  variant?: "default" | "outline" | "secondary" | "destructive" | "ghost" | "link"
  className?: string
}

export function StripeCheckout({ 
  planId, 
  planName, 
  isAnnual, 
  buttonText = "Pay Now", 
  variant = "default",
  className = ""
}: StripeCheckoutProps) {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { isLoaded, user } = useUser();
  
  // Check if the user is authenticated based on Clerk's user state
  const isAuthenticated = isLoaded && !!user;

  const handleCheckout = async () => {
    setIsLoading(true);

    try {
      // For all plans, check authentication first
      if (!isAuthenticated) {
        // Store the intended plan for after login
        localStorage.setItem('pendingPlan', planId);
        localStorage.setItem('pendingBilling', isAnnual ? 'annual' : 'monthly');
        
        // Redirect to login with a redirect to checkout page, not pricing page
        router.push(`/sign-in?redirectUrl=${encodeURIComponent(`/checkout?plan=${planId}&billing=${isAnnual ? 'annual' : 'monthly'}`)}`);
        return;
      }

      // Now handle specific cases
      if (planId === 'free') {
        router.push('/dashboard');
        return;
      }

      // If this is a "Contact Sales" button, redirect to contact page
      if ((buttonText || '').toLowerCase().includes('contact sales')) {
        router.push('/contact');
        return;
      }

      // For all paid plans, redirect to the checkout page
      // This ensures a consistent experience whether coming from pricing or billing
      router.push(`/checkout?plan=${planId}&billing=${isAnnual ? 'annual' : 'monthly'}`);
    } catch (error) {
      console.error('Error during checkout:', error);
      alert('Something went wrong with the checkout process. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button 
      onClick={handleCheckout} 
      disabled={isLoading} 
      variant={variant}
      className={className}
    >
      {isLoading ? 'Processing...' : buttonText || 'Pay Now'}
    </Button>
  )
} 