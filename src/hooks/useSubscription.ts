import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import useSWR from 'swr';

export type Subscription = {
  status: string;
  plan: string;
  isAnnual: boolean;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
  subscriptionId?: string;
  derivedStatus?: string;
};

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const error = new Error('An error occurred while fetching the data.');
    throw error;
  }
  return res.json();
};

/**
 * Custom hook to fetch and cache the user's subscription data
 * Uses SWR for efficient data fetching and caching
 */
export function useSubscription() {
  const { isSignedIn, user } = useUser();
  const [hasMounted, setHasMounted] = useState(false);
  
  // Only start fetching after component mounts to avoid hydration issues
  useEffect(() => {
    setHasMounted(true);
  }, []);
  
  // Don't fetch if not signed in or component hasn't mounted yet
  const shouldFetch = isSignedIn && hasMounted;
  
  const { data, error, isLoading, mutate } = useSWR(
    shouldFetch ? '/api/subscriptions' : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60000, // 1 minute
    }
  );
  
  // Default subscription data for free tier
  const defaultSubscription: Subscription = {
    status: 'inactive',
    plan: 'free',
    isAnnual: false,
    currentPeriodEnd: null,
    cancelAtPeriodEnd: false,
  };
  
  // Extract subscription from response or use default
  const subscription = data?.subscription || defaultSubscription;
  
  // Derive status for UI that shows "cancelling" when appropriate
  if (!subscription.derivedStatus) {
    if (subscription.status === 'active' && subscription.cancelAtPeriodEnd === true) {
      subscription.derivedStatus = 'cancelling';
    } else {
      subscription.derivedStatus = subscription.status;
    }
  }
  
  // Helper function to check if user has an active paid subscription
  const isSubscribed = (): boolean => {
    return (
      subscription.status === 'active' && 
      (subscription.plan === 'pro' || subscription.plan === 'advanced')
    );
  };
  
  // Helper function to check if subscription is set to cancel
  const isCancelling = (): boolean => {
    return subscription.cancelAtPeriodEnd === true;
  };
  
  // Helper to get days remaining in subscription
  const daysRemaining = (): number | null => {
    if (!subscription.currentPeriodEnd) return null;
    
    const endDate = new Date(subscription.currentPeriodEnd);
    
    // Check for invalid dates (like epoch 0 or very old dates)
    if (isNaN(endDate.getTime()) || endDate.getFullYear() < 2000) {
      return null;
    }
    
    const now = new Date();
    const diffTime = endDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
  };
  
  const cancelSubscription = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/subscriptions/cancel', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to cancel subscription');
      }
      
      const data = await response.json();
      
      // Create a new subscription object with updated data
      const updatedSubscription = {
        ...subscription,
        ...data.subscription,
        cancelAtPeriodEnd: true // Ensure this property is set correctly
      };
      
      // Update the local cache with the new subscription data
      mutate({ subscription: updatedSubscription }, { revalidate: false });
      
      return true;
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      return false;
    }
  };
  
  const reactivateSubscription = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/subscriptions/reactivate', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to reactivate subscription');
      }
      
      const data = await response.json();
      
      // Create a new subscription object with updated data, ensuring cancelAtPeriodEnd is false
      const updatedSubscription = {
        ...subscription,
        ...data.subscription,
        cancelAtPeriodEnd: false // Ensure this property is set correctly
      };
      
      // Update the local cache with the new subscription data
      mutate({ subscription: updatedSubscription }, { revalidate: false });
      
      return true;
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      return false;
    }
  };
  
  return {
    subscription,
    isLoading: isLoading || !hasMounted,
    error,
    isSubscribed,
    isCancelling,
    daysRemaining,
    cancelSubscription,
    reactivateSubscription,
    mutate,
  };
} 