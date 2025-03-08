"use client"

import { useState, useEffect } from "react"
import { useUser } from "@clerk/nextjs"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Loader2, Save } from "lucide-react"
import Link from "next/link"
import { toast } from "@/components/ui/use-toast"

export default function ProfilePage() {
  const { isLoaded, user } = useUser();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
  });
  
  useEffect(() => {
    if (!isLoaded) return;
    
    if (!user) {
      router.push("/sign-in");
      return;
    }
    
    // Initialize form data with Clerk user data
    setFormData({
      firstName: user.firstName || "",
      lastName: user.lastName || "",
      email: user.primaryEmailAddress?.emailAddress || "",
    });
    
    setIsLoading(false);
  }, [isLoaded, user, router]);
  
  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      // Make API call to update user
      const response = await fetch("/api/auth/user", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          firstName: formData.firstName,
          lastName: formData.lastName,
        }),
      });
      
      if (!response.ok) throw new Error("Failed to update profile");
      
      // Update Clerk user object in UI
      if (user) {
        await user.update({
          firstName: formData.firstName,
          lastName: formData.lastName,
        });
      }
      
      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully.",
      });
    } catch (error) {
      console.error("Error updating profile:", error);
      toast({
        title: "Error",
        description: "Failed to update your profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  if (!isLoaded || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }
  
  // Format creation date properly
  const accountCreated = user?.createdAt ? new Date(user.createdAt) : null;
  const formattedCreationDate = accountCreated ? 
    accountCreated.toLocaleDateString("en-US", {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }) : "N/A";
  
  return (
    <div className="container mx-auto py-10 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings and preferences
        </p>
      </div>
      
      <div className="grid gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Profile Details</CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input 
                    id="firstName" 
                    placeholder="First name" 
                    value={formData.firstName} 
                    onChange={(e) => setFormData({ ...formData, firstName: e.target.value })} 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input 
                    id="lastName" 
                    placeholder="Last name" 
                    value={formData.lastName} 
                    onChange={(e) => setFormData({ ...formData, lastName: e.target.value })} 
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="Email" 
                  value={formData.email} 
                  disabled
                />
                <p className="text-xs text-muted-foreground">
                  Email changes are managed through your Clerk account
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="account-id">Account ID</Label>
                  <Input 
                    id="account-id" 
                    value={user?.id || ""} 
                    disabled
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="created-at">Account Created</Label>
                  <Input 
                    id="created-at" 
                    value={formattedCreationDate} 
                    disabled
                  />
                </div>
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button 
              onClick={handleSaveProfile}
              disabled={isSaving}
            >
              {isSaving ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving</>
              ) : (
                <><Save className="mr-2 h-4 w-4" /> Save Changes</>
              )}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Subscription</CardTitle>
            <CardDescription>Manage your subscription and billing</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              View and manage your subscription details, billing history, and payment methods.
            </p>
          </CardContent>
          <CardFooter>
            <Button asChild variant="outline">
              <Link href="/profile/billing">Manage Subscription</Link>
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Security</CardTitle>
            <CardDescription>Manage your account security</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              For security settings including password changes and two-factor authentication, please visit your Clerk account dashboard.
            </p>
          </CardContent>
          <CardFooter>
            <Button asChild variant="outline">
              <a href="https://accounts.clerk.dev/user/security" target="_blank" rel="noopener noreferrer">
                Security Settings
              </a>
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
} 