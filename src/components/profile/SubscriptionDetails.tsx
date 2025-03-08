"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import useSWR from 'swr';

// Fetcher function for SWR
const fetcher = (url: string) => fetch(url).then(res => res.json());

export function SubscriptionDetails() {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const { data, error, mutate } = useSWR('/api/subscriptions', fetcher);
  
  const subscription = data?.subscription;
  const isActive = subscription?.status === 'active' || subscription?.status === 'trialing';

  const handleCancelSubscription = async () => {
    setIsLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('/api/subscriptions/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Error cancelling subscription');
      }
      
      setMessage({
        type: 'success',
        text: "Your subscription will end at the current billing period."
      });
      
      // Refresh subscription data
      mutate();
    } catch (error) {
      console.error('Error:', error);
      setMessage({
        type: 'error',
        text: "There was an error cancelling your subscription. Please try again later."
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Subscription</CardTitle>
        <CardDescription>Your current subscription plan</CardDescription>
      </CardHeader>
      <CardContent>
        {message && (
          <div className={`p-3 mb-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {message.text}
          </div>
        )}
        
        {!data ? (
          <div className="h-20 w-full bg-gray-200 animate-pulse rounded-md"></div>
        ) : !subscription ? (
          <div>
            <p>You don't have an active subscription.</p>
            <Button asChild className="mt-4">
              <a href="/pricing">View Plans</a>
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Plan:</span>
              <span className="capitalize">{subscription.plan}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Status:</span>
              <span className="capitalize">{subscription.status}</span>
            </div>
            {subscription.isAnnual !== undefined && (
              <div className="flex justify-between">
                <span className="font-medium">Billing period:</span>
                <span>{subscription.isAnnual ? 'Annual' : 'Monthly'}</span>
              </div>
            )}
            {isActive && subscription.currentPeriodEnd && (
              <div className="flex justify-between">
                <span className="font-medium">Renews on:</span>
                <span>{new Date(subscription.currentPeriodEnd).toLocaleDateString()}</span>
              </div>
            )}
            {subscription.cancelAtPeriodEnd && subscription.currentPeriodEnd && (
              <div className="mt-4 p-3 bg-yellow-50 text-yellow-800 rounded-md">
                Your subscription will end on {new Date(subscription.currentPeriodEnd).toLocaleDateString()}.
              </div>
            )}
          </div>
        )}
      </CardContent>
      {isActive && subscription && !subscription.cancelAtPeriodEnd && (
        <CardFooter>
          <Button 
            variant="outline" 
            onClick={handleCancelSubscription} 
            disabled={isLoading}
          >
            {isLoading ? 'Cancelling...' : 'Cancel Subscription'}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
} 