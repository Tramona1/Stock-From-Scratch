"use client"

import { Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { CheckCircle } from "lucide-react"
import { useUser } from "@clerk/nextjs"

// Add this at the top of the file
export const dynamic = 'force-dynamic';

// Create a loading component
function SuccessLoading() {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 py-12">
        <div className="container max-w-lg">
          <div className="animate-pulse space-y-6 text-center">
            <div className="h-20 w-20 bg-gray-200 rounded-full mx-auto"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded w-1/3 mx-auto"></div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Content component that uses useSearchParams
function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, isLoaded } = useUser();
  const [isUpdating, setIsUpdating] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const plan = searchParams.get("plan") || "Pro";
  const isAnnual = searchParams.get("annual") === "true";
  const sessionId = searchParams.get("session_id");
  
  useEffect(() => {
    const updateSubscription = async () => {
      if (!isLoaded || !user) return;
      
      try {
        setIsUpdating(true);
        
        console.log(`Success page: Activating subscription for user ${user.id}, session: ${sessionId}`);
        
        // Call an API to force update the subscription status
        const response = await fetch('/api/subscriptions/activate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sessionId,
            plan: plan || 'pro',
            isAnnual: isAnnual || false
          }),
        });
        
        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(result.error || 'Failed to activate subscription');
        }
        
        console.log('Subscription activation successful:', result);
        
        // Save subscription info to localStorage as a backup
        const subscription = {
          plan: plan,
          status: "active",
          currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          cancelAtPeriodEnd: false
        };
        
        localStorage.setItem("subscription", JSON.stringify(subscription));
      } catch (err) {
        console.error("Error updating subscription:", err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setIsUpdating(false);
      }
    };
    
    updateSubscription();
  }, [isLoaded, user, sessionId, plan, isAnnual]);
  
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 py-12">
        <div className="container max-w-lg text-center">
          <div className="flex justify-center mb-6">
            <div className="rounded-full bg-green-100 p-4">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
          </div>
          
          <h1 className="text-3xl font-bold mb-4">Payment Successful!</h1>
          
          <p className="text-lg mb-8">
            Thank you for subscribing to our {plan} plan. You now have access to all {plan} features.
            {isAnnual ? " Your annual subscription is now active." : " Your monthly subscription is now active."}
          </p>
          
          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6">
              {error}
              <p className="text-sm mt-2">
                Don't worry, your payment was processed successfully and our team will ensure your subscription is activated.
              </p>
            </div>
          )}
          
          <Button 
            size="lg" 
            onClick={() => router.push("/dashboard")}
            disabled={isUpdating}
          >
            {isUpdating ? "Finalizing subscription..." : "Go to Dashboard"}
          </Button>
        </div>
      </main>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<SuccessLoading />}>
      <SuccessContent />
    </Suspense>
  );
} 