"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { 
  AlertCircle, 
  CheckCircle2, 
  CreditCard, 
  HelpCircle, 
  Package, 
  RefreshCw,
  AlertTriangle,
  XCircle,
  Loader2,
  Info
} from "lucide-react"
import Link from "next/link"
import { useUser } from "@clerk/nextjs"
import { StripeCheckout } from "@/components/payment/StripeCheckout"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { toast } from "@/components/ui/use-toast"

// Define the subscription type
interface Subscription {
  plan: string;
  status: string;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
  derivedStatus?: string;
}

export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { isLoaded, user } = useUser()

  // Fetch real subscription data from API
  useEffect(() => {
    const fetchSubscription = async () => {
      setIsLoading(true);
      try {
        console.log("Fetching subscription data...");
        const response = await fetch('/api/subscriptions', {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        
        if (!response.ok) {
          console.error(`Error fetching subscription: ${response.status} ${response.statusText}`);
          // If we get a 404 (user not found), set default inactive subscription
          if (response.status === 404) {
            console.log("User not found in database, using default subscription");
            setSubscription({
              plan: 'free',
              status: 'inactive',
              currentPeriodEnd: null,
              cancelAtPeriodEnd: false,
              derivedStatus: 'inactive'
            });
          }
          setIsLoading(false);
          return;
        }
        
        const data = await response.json();
        
        console.log('Received subscription data:', JSON.stringify(data));
        
        if (data.subscription) {
          setSubscription({
            plan: data.subscription.plan,
            status: data.subscription.status,
            currentPeriodEnd: data.subscription.currentPeriodEnd,
            // Explicitly convert to boolean
            cancelAtPeriodEnd: data.subscription.cancelAtPeriodEnd === true,
            derivedStatus: data.subscription.derivedStatus || data.subscription.status
          });
        } else {
          // Default to inactive if no subscription is found
          console.log("No subscription data returned, using default subscription");
          setSubscription({
            plan: 'free',
            status: 'inactive',
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            derivedStatus: 'inactive'
          });
        }
      } catch (error) {
        console.error('Error fetching subscription data:', error);
        // Use fallback from localStorage if available
        const storedSubscription = localStorage.getItem('subscription');
        if (storedSubscription) {
          try {
            const parsed = JSON.parse(storedSubscription);
            setSubscription(parsed);
            console.log('Using cached subscription data from localStorage');
          } catch (parseError) {
            console.error('Error parsing stored subscription:', parseError);
          }
        } else {
          // Default to inactive if no subscription is found
          setSubscription({
            plan: 'free',
            status: 'inactive',
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            derivedStatus: 'inactive'
          });
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSubscription();
  }, [isLoaded, user]);

  const formatDate = (dateString: string | null) => {
    // If the date is null or undefined, return "N/A"
    if (!dateString) return "N/A";
    
    // Check if it's a valid date
    const date = new Date(dateString);
    
    // Check for invalid date (e.g., timestamp 0 which might show as Dec 31, 1969)
    if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
      return "N/A";
    }
    
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 py-12">
        <div className="container max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">Subscription Management</h1>
          
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded-lg mb-6"></div>
              <div className="h-64 bg-gray-200 rounded-lg"></div>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {/* Current Plan */}
              {subscription?.status === "active" && subscription?.cancelAtPeriodEnd && (
                <Alert className="mb-4 border-yellow-200 bg-yellow-50 text-yellow-800">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Subscription set to cancel</AlertTitle>
                  <AlertDescription>
                    Your subscription will remain active until{" "}
                    {formatDate(subscription.currentPeriodEnd)}. You can reactivate
                    your subscription at any time before then.
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Display only for non-logged in users or those with no subscription */}
              {(subscription?.status === "inactive" || !subscription) && (
                <Alert className="mb-4">
                  <Info className="h-4 w-4" />
                  <AlertTitle>No active subscription</AlertTitle>
                  <AlertDescription>
                    Subscribe to access premium features and support the development of this app.
                  </AlertDescription>
                </Alert>
              )}
              
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Current Plan
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="ml-auto"
                      onClick={() => {
                        setIsLoading(true);
                        fetch('/api/subscriptions', {
                          cache: 'no-store',
                          headers: {
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                          }
                        })
                        .then(res => res.json())
                        .then(data => {
                          if (data.subscription) {
                            console.log('Refreshed subscription data:', JSON.stringify(data.subscription));
                            setSubscription({
                              plan: data.subscription.plan,
                              status: data.subscription.status,
                              currentPeriodEnd: data.subscription.currentPeriodEnd,
                              // Explicitly convert to boolean
                              cancelAtPeriodEnd: data.subscription.cancelAtPeriodEnd === true
                            });
                          }
                          setIsLoading(false);
                        })
                        .catch(err => {
                          console.error('Error refreshing subscription:', err);
                          setIsLoading(false);
                        });
                      }}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    Details about your current subscription
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {subscription ? (
                    <div className="space-y-4">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Plan</span>
                        <span className="font-medium">{subscription.plan}</span>
                      </div>
                      <div className="flex justify-between">
                        <Label>Status</Label>
                        <div className="flex items-center gap-2">
                          {subscription?.derivedStatus === "cancelling" ? (
                            <>
                              <AlertTriangle className="h-4 w-4 text-yellow-500" />
                              <span className="font-medium text-yellow-500">Active (Cancelling)</span>
                            </>
                          ) : subscription?.status === "active" ? (
                            <>
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              <span className="font-medium text-green-500">Active</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 text-destructive" />
                              <span className="font-medium text-destructive">Inactive</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Billing Period Ends</span>
                        <span className="font-medium">{formatDate(subscription.currentPeriodEnd)}</span>
                      </div>
                      {subscription.cancelAtPeriodEnd && (
                        <div className="rounded-md bg-yellow-50 p-4 mt-4">
                          <div className="flex">
                            <div className="flex-shrink-0">
                              <AlertCircle className="h-5 w-5 text-yellow-400" />
                            </div>
                            <div className="ml-3">
                              <h3 className="text-sm font-medium text-yellow-800">Cancellation scheduled</h3>
                              <div className="mt-2 text-sm text-yellow-700">
                                <p>
                                  Your subscription will be cancelled on {formatDate(subscription.currentPeriodEnd)}.
                                  You'll have access to all features until then.
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <p className="text-muted-foreground mb-4">You don't have an active subscription</p>
                      <Link href="/pricing">
                        <Button>View Plans</Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex flex-col space-y-4">
                  {subscription?.status === "active" ? (
                    subscription?.cancelAtPeriodEnd ? (
                      <Button
                        className="w-full"
                        onClick={async () => {
                          setIsLoading(true)
                          try {
                            const response = await fetch("/api/subscriptions/reactivate", {
                              method: "POST",
                              headers: {
                                "Content-Type": "application/json",
                              },
                            })
                            const data = await response.json()
                            if (data.success) {
                              console.log("Subscription reactivated successfully")
                              // Update the subscription state
                              setSubscription({
                                ...subscription,
                                cancelAtPeriodEnd: false
                              })
                              toast({
                                title: "Subscription reactivated",
                                description: "Your subscription has been reactivated",
                              })
                            } else {
                              console.error("Failed to reactivate subscription", data.error)
                              toast({
                                title: "Error",
                                description: data.error || "Failed to reactivate subscription",
                                variant: "destructive",
                              })
                            }
                          } catch (error) {
                            console.error("Error reactivating subscription:", error)
                            toast({
                              title: "Error",
                              description: "An unexpected error occurred",
                              variant: "destructive",
                            })
                          } finally {
                            setIsLoading(false)
                          }
                        }}
                      >
                        {isLoading ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : null}
                        Reactivate Subscription
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={async () => {
                          setIsLoading(true)
                          try {
                            const response = await fetch("/api/subscriptions/cancel", {
                              method: "POST",
                              headers: {
                                "Content-Type": "application/json",
                              },
                            })
                            const data = await response.json()
                            if (data.success) {
                              console.log("Subscription cancelled successfully")
                              // Update the subscription state
                              setSubscription({
                                ...subscription,
                                cancelAtPeriodEnd: true
                              })
                              toast({
                                title: "Subscription cancelled",
                                description: "Your subscription will end at the end of the billing period",
                              })
                            } else {
                              console.error("Failed to cancel subscription", data.error)
                              toast({
                                title: "Error",
                                description: data.error || "Failed to cancel subscription",
                                variant: "destructive",
                              })
                            }
                          } catch (error) {
                            console.error("Error cancelling subscription:", error)
                            toast({
                              title: "Error",
                              description: "An unexpected error occurred",
                              variant: "destructive",
                            })
                          } finally {
                            setIsLoading(false)
                          }
                        }}
                      >
                        {isLoading ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : null}
                        Cancel Subscription
                      </Button>
                    )
                  ) : (
                    <div className="space-y-4">
                      <div className="text-sm text-muted-foreground">
                        Subscribe to access premium features.
                      </div>
                      <StripeCheckout 
                        planId="pro"
                        planName="Pro"
                        isAnnual={false}
                        buttonText="Subscribe Now"
                        className="w-full"
                      />
                    </div>
                  )}
                </CardFooter>
              </Card>

              {/* Payment Methods & Support */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CreditCard className="h-5 w-5" />
                      Payment Method
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-16 bg-gray-100 rounded flex items-center justify-center">
                          <span className="text-sm font-medium">VISA</span>
                        </div>
                        <div>
                          <p className="font-medium">•••• 4242</p>
                          <p className="text-sm text-muted-foreground">Expires 12/2025</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">Update</Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="h-5 w-5" />
                      Need Help?
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4">
                      Have questions about your billing or need assistance with your subscription?
                    </p>
                    <a href={`mailto:blakesingleton@hotmail.com?subject=Billing%20Support%20Request`}>
                      <Button variant="outline" className="w-full">
                        Contact Support
                      </Button>
                    </a>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
} 