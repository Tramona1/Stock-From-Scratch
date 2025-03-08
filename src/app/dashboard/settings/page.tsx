"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useUser } from "@clerk/nextjs"
import { useAuth } from "@/hooks/useAuth"

export default function SettingsPage() {
  const { user } = useUser()
  const { userData } = useAuth()
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    darkMode: false,
    notifications: true,
  })

  useEffect(() => {
    if (user) {
      setFormData({
        ...formData,
        firstName: user.firstName || "",
        lastName: user.lastName || "",
        email: user.primaryEmailAddress?.emailAddress || "",
      })
    }

    if (userData) {
      setFormData(prev => ({
        ...prev,
        darkMode: userData?.preferences?.darkMode || false,
        notifications: userData?.preferences?.notifications || true,
      }))
    }
  }, [user, userData])

  async function handleSaveProfile() {
    try {
      const response = await fetch("/api/auth/user", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          firstName: formData.firstName,
          lastName: formData.lastName,
          preferences: {
            darkMode: formData.darkMode,
            notifications: formData.notifications,
          },
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to update profile")
      }

      alert("Profile updated successfully")
    } catch (error) {
      console.error("Error updating profile:", error)
      alert("Failed to update profile")
    }
  }

  return (
    <div className="container p-6 space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>
      
      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>
        
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input 
                    id="firstName" 
                    value={formData.firstName}
                    onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input 
                    id="lastName" 
                    value={formData.lastName}
                    onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" value={formData.email} disabled />
                <p className="text-xs text-muted-foreground">Email cannot be changed directly. Please contact support.</p>
              </div>
              <Button onClick={handleSaveProfile}>Save Profile</Button>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="preferences">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox id="alerts" defaultChecked />
                  <Label htmlFor="alerts">Price Alerts</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="news" defaultChecked />
                  <Label htmlFor="news">Breaking News</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="earnings" defaultChecked />
                  <Label htmlFor="earnings">Earnings Announcements</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="insider" />
                  <Label htmlFor="insider">Insider Trading</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="newsletter" />
                  <Label htmlFor="newsletter">Weekly Newsletter</Label>
                </div>
              </div>
              
              <Button className="mt-6">Save Preferences</Button>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox id="alerts" defaultChecked />
                  <Label htmlFor="alerts">Price Alerts</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="news" defaultChecked />
                  <Label htmlFor="news">Breaking News</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="earnings" defaultChecked />
                  <Label htmlFor="earnings">Earnings Announcements</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="insider" />
                  <Label htmlFor="insider">Insider Trading</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="newsletter" />
                  <Label htmlFor="newsletter">Weekly Newsletter</Label>
                </div>
              </div>
              
              <Button className="mt-6">Save Preferences</Button>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="api">
          <Card>
            <CardHeader>
              <CardTitle>API Integration</CardTitle>
            </CardHeader>
            <CardContent>
              <p>API key management will appear here.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 