"use client"

import React, { useState, useEffect } from 'react'
import { CheckIcon } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { StripeCheckout } from "@/components/payment/StripeCheckout"
import { useUser } from "@clerk/nextjs"

const tiers = [
  {
    name: "Free",
    id: "free",
    price: "$0",
    annualPrice: "$0",
    description: "Essential tools for casual investors",
    features: [
      "Real-time market indicators",
      "Basic stock watchlist",
      "Daily market summaries",
      "Limited market news feed",
      "Basic technical indicators"
    ],
    cta: "Get Started",
    ctaLink: "/sign-up",
    mostPopular: false
  },
  {
    name: "Pro",
    id: "pro",
    price: "$14.99",
    annualPrice: "$143.90",
    description: "Advanced analytics for active traders",
    features: [
      "Everything in Free",
      "Advanced technical analysis",
      "AI-powered stock suggestions",
      "Portfolio performance tracking",
      "Custom alerts and notifications",
      "Priority customer support",
      "Watchlist for up to 100 stocks"
    ],
    cta: "Start 7-Day Free Trial",
    ctaLink: "/sign-up?plan=pro",
    mostPopular: true
  },
  {
    name: "Advanced",
    id: "advanced",
    price: "$29.99",
    annualPrice: "$287.90",
    description: "Complete solution for professional traders",
    features: [
      "Everything in Pro",
      "Advanced AI market analysis",
      "Unlimited watchlists",
      "Custom strategy backtesting",
      "API access",
      "White-label options",
      "Dedicated account manager",
      "Custom integrations"
    ],
    cta: "Contact Sales",
    ctaLink: "/contact",
    mostPopular: false
  }
]

const frequentlyAskedQuestions = [
  {
    question: "How does the 7-day free trial work?",
    answer: "You can sign up for the Pro plan and try it free for 7 days. You won't be charged until the trial period ends, and you can cancel anytime before then."
  },
  {
    question: "Can I upgrade or downgrade my plan later?",
    answer: "Yes, you can upgrade or downgrade your subscription at any time. When upgrading, you'll get immediate access to the new features. When downgrading, changes will take effect at the end of your billing cycle."
  },
  {
    question: "What payment methods do you accept?",
    answer: "We accept all major credit cards (Visa, Mastercard, American Express) as well as PayPal for subscription payments."
  },
  {
    question: "Is there a discount for annual billing?",
    answer: "Yes, you can save 20% by choosing annual billing for any of our paid plans."
  },
  {
    question: "Do you offer educational resources?",
    answer: "Yes, all plans include access to our basic educational library. Pro and Enterprise plans include premium educational content and webinars."
  }
]

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false)
  const [currentPlan, setCurrentPlan] = useState<string | null>(null)
  const { isLoaded, isSignedIn } = useUser()
  
  useEffect(() => {
    // Fetch the user's current subscription plan when component mounts
    const fetchSubscription = async () => {
      if (isSignedIn) {
        try {
          const response = await fetch('/api/subscriptions', {
            headers: { 'Cache-Control': 'no-cache' }
          });
          
          if (response.ok) {
            const data = await response.json();
            setCurrentPlan(data.subscription?.plan?.toLowerCase() || 'free');
          } else {
            setCurrentPlan('free');
          }
        } catch (error) {
          console.error('Error fetching subscription:', error);
          setCurrentPlan('free');
        }
      } else {
        setCurrentPlan(null);
      }
    };
    
    if (isLoaded) {
      fetchSubscription();
    }
  }, [isLoaded, isSignedIn]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="py-12 sm:py-16 lg:py-20">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-4xl text-center">
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
                Simple, transparent pricing
              </h1>
              <p className="mt-6 text-xl text-muted-foreground">
                Choose the perfect plan for your investment journey
              </p>
            </div>
            
            {/* Pricing Toggle */}
            <div className="mt-10 flex justify-center">
              <div className="relative flex rounded-lg bg-gray-100 p-1">
                <button 
                  onClick={() => setIsAnnual(false)}
                  className={cn(
                    "py-1 px-3 text-sm",
                    !isAnnual ? "bg-white rounded-md shadow-sm font-medium" : "text-muted-foreground"
                  )}
                >
                  Monthly billing
                </button>
                <button 
                  onClick={() => setIsAnnual(true)}
                  className={cn(
                    "py-1 px-3 text-sm",
                    isAnnual ? "bg-white rounded-md shadow-sm font-medium" : "text-muted-foreground"
                  )}
                >
                  Annual billing <span className="text-blue-600">(save 20%)</span>
                </button>
              </div>
            </div>

            {/* Pricing Cards */}
            <div className="mx-auto mt-12 grid max-w-md grid-cols-1 gap-8 lg:max-w-5xl lg:grid-cols-3">
              {tiers.map((tier) => (
                <div 
                  key={tier.id}
                  className={cn(
                    "flex flex-col justify-between rounded-xl bg-white p-8 shadow-sm border border-gray-200 xl:p-8 relative",
                    tier.mostPopular ? "border-blue-100 shadow-md" : ""
                  )}
                >
                  <div>
                    <div className="flex items-center justify-between gap-x-4">
                      <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                      {tier.mostPopular && (
                        <div className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                          Most Popular
                        </div>
                      )}
                    </div>
                    <p className="mt-4 flex items-baseline gap-x-1">
                      <span className="text-4xl font-bold tracking-tight text-gray-900">
                        {isAnnual ? tier.annualPrice : tier.price}
                      </span>
                      <span className="text-sm font-semibold text-muted-foreground">
                        {isAnnual ? '/year' : '/month'}
                      </span>
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">{tier.description}</p>
                    <ul className="mt-6 space-y-3 text-sm">
                      {tier.features.map((feature) => (
                        <li key={feature} className="flex gap-x-3">
                          <CheckIcon className="h-5 w-5 flex-none text-blue-500" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  {tier.id === currentPlan ? (
                    <Button 
                      variant="outline" 
                      className="w-full py-5 cursor-default"
                      disabled
                    >
                      Current Plan
                    </Button>
                  ) : tier.id === 'free' ? (
                    <Button
                      asChild
                      variant={tier.mostPopular ? "default" : "outline"}
                      className="w-full py-5"
                    >
                      <Link href="/sign-up">Get Started</Link>
                    </Button>
                  ) : (
                    <StripeCheckout
                      planId={tier.id}
                      planName={tier.name}
                      isAnnual={isAnnual}
                      buttonText="Pay Now"
                      variant={tier.mostPopular ? "default" : "outline"}
                      className="w-full py-5"
                    />
                  )}
                </div>
              ))}
            </div>
            
            {/* Feature Comparison */}
            <div className="mx-auto mt-24 max-w-5xl">
              <h2 className="text-2xl font-bold text-center mb-12">Compare Features</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 bg-gray-50 text-left text-sm font-semibold text-gray-900 w-1/3">Feature</th>
                      <th className="px-6 py-3 bg-gray-50 text-center text-sm font-semibold text-gray-900">Free</th>
                      <th className="px-6 py-3 bg-gray-50 text-center text-sm font-semibold text-gray-900 bg-blue-50">Pro</th>
                      <th className="px-6 py-3 bg-gray-50 text-center text-sm font-semibold text-gray-900">Advanced</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">Market Indicators</td>
                      <td className="px-6 py-4 text-center">Basic</td>
                      <td className="px-6 py-4 text-center bg-blue-50">Advanced</td>
                      <td className="px-6 py-4 text-center">Full Access</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">Watchlist Size</td>
                      <td className="px-6 py-4 text-center">Up to 10 stocks</td>
                      <td className="px-6 py-4 text-center bg-blue-50">Up to 100 stocks</td>
                      <td className="px-6 py-4 text-center">Unlimited</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">AI Stock Analysis</td>
                      <td className="px-6 py-4 text-center">❌</td>
                      <td className="px-6 py-4 text-center bg-blue-50">✅</td>
                      <td className="px-6 py-4 text-center">✅</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">Custom Alerts</td>
                      <td className="px-6 py-4 text-center">❌</td>
                      <td className="px-6 py-4 text-center bg-blue-50">Up to 10</td>
                      <td className="px-6 py-4 text-center">Unlimited</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">API Access</td>
                      <td className="px-6 py-4 text-center">❌</td>
                      <td className="px-6 py-4 text-center bg-blue-50">❌</td>
                      <td className="px-6 py-4 text-center">✅</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">Priority Support</td>
                      <td className="px-6 py-4 text-center">❌</td>
                      <td className="px-6 py-4 text-center bg-blue-50">✅</td>
                      <td className="px-6 py-4 text-center">✅</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* FAQs */}
            <div className="mx-auto max-w-4xl mt-24">
              <h2 className="text-2xl font-bold text-center mb-12">Frequently Asked Questions</h2>
              <dl className="divide-y divide-gray-200">
                {frequentlyAskedQuestions.map((faq, index) => (
                  <div key={index} className="py-6">
                    <dt className="text-lg font-medium text-gray-900">{faq.question}</dt>
                    <dd className="mt-2 text-base text-muted-foreground">{faq.answer}</dd>
                  </div>
                ))}
              </dl>
            </div>
            
            {/* CTA */}
            <div className="mt-24 rounded-xl bg-blue-600 p-10 text-center">
              <h3 className="text-2xl font-bold tracking-tight text-white">Ready to get started?</h3>
              <p className="mt-6 text-lg leading-8 text-white/80">
                Join thousands of traders who are already using StockAI to make smarter investment decisions.
              </p>
              <div className="mt-10 flex justify-center gap-x-6">
                <Link href="/sign-up">
                  <Button variant="secondary" size="lg">
                    Create your account
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button variant="outline" className="bg-transparent text-white border-white hover:bg-white/10" size="lg">
                    Contact sales
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 