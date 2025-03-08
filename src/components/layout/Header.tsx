"use client"

import React, { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LogOut,
  Menu,
  X,
  Settings,
  CreditCard,
  UserCircle,
  HelpCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { SignInButton, SignUpButton, useUser, useClerk } from "@clerk/nextjs"

export function Header() {
  const pathname = usePathname()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const { isSignedIn, user, isLoaded } = useUser()
  const { signOut } = useClerk()
  
  const navigation = [
    { name: "Dashboard", href: "/dashboard" },
    { name: "Pricing", href: "/pricing" },
  ]
  
  // Handle clicks outside of the dropdown
  React.useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (profileMenuOpen) {
        const dropdown = document.getElementById('profile-dropdown');
        const button = document.getElementById('profile-button');
        
        if (dropdown && button && 
            !dropdown.contains(event.target as Node) && 
            !button.contains(event.target as Node)) {
          setProfileMenuOpen(false);
        }
      }
    };
    
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [profileMenuOpen]);
  
  const handleSignOut = async () => {
    await signOut();
    // Redirect to home page after signing out
    window.location.href = '/';
  }
  
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-bold text-xl">
            StockAI
          </Link>
          
          <nav className="hidden md:flex gap-6">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-primary",
                  pathname === item.href
                    ? "text-foreground"
                    : "text-foreground/60"
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
        
        <div className="md:hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          {isLoaded ? (
            isSignedIn ? (
              <div className="relative">
                <Button 
                  id="profile-button"
                  variant="ghost" 
                  size="sm"
                  className="flex items-center gap-1 rounded-full h-10 w-10 justify-center"
                  onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                >
                  {user.imageUrl ? (
                    <img 
                      src={user.imageUrl} 
                      alt={user.fullName || "User profile"} 
                      className="h-8 w-8 rounded-full object-cover"
                    />
                  ) : (
                    <UserCircle className="h-6 w-6" />
                  )}
                </Button>
                
                {/* Simple dropdown without the Radix component */}
                {profileMenuOpen && (
                  <div 
                    id="profile-dropdown"
                    className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
                  >
                    <div className="py-1">
                      <div className="px-4 py-2 text-sm font-medium border-b border-gray-100">
                        {user.fullName || "My Account"}
                      </div>
                      
                      <Link 
                        href="/profile" 
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <UserCircle className="mr-2 h-5 w-5" />
                        Profile
                      </Link>
                      
                      <Link 
                        href="/profile/billing" 
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <CreditCard className="mr-2 h-5 w-5" />
                        Billing
                      </Link>
                      
                      <Link 
                        href="/dashboard/settings" 
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <Settings className="mr-2 h-5 w-5" />
                        Settings
                      </Link>
                      
                      <Link 
                        href="/help" 
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <HelpCircle className="mr-2 h-5 w-5" />
                        Help
                      </Link>
                      
                      <div className="border-t border-gray-100 my-1"></div>
                      
                      <button
                        onClick={handleSignOut}
                        className="flex w-full items-center px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                      >
                        <LogOut className="mr-2 h-5 w-5" />
                        Log out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <>
                <SignInButton mode="modal">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <Button variant="default" size="sm">
                    Sign Up
                  </Button>
                </SignUpButton>
              </>
            )
          ) : (
            <div className="h-10 w-10 rounded-full bg-gray-200 animate-pulse"></div>
          )}
        </div>
      </div>
      
      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="space-y-1 px-2 pb-3 pt-2">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "block rounded-md px-3 py-2 text-base font-medium",
                  pathname === item.href 
                    ? "bg-primary/10 text-primary" 
                    : "text-foreground/70 hover:bg-primary/10 hover:text-primary"
                )}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            {isSignedIn && (
              <>
                <Link
                  href="/profile"
                  className="block rounded-md px-3 py-2 text-base font-medium text-foreground/70 hover:bg-primary/10 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Profile
                </Link>
                <Link
                  href="/profile/billing"
                  className="block rounded-md px-3 py-2 text-base font-medium text-foreground/70 hover:bg-primary/10 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Billing
                </Link>
                <Link
                  href="/dashboard/settings"
                  className="block rounded-md px-3 py-2 text-base font-medium text-foreground/70 hover:bg-primary/10 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Settings
                </Link>
                <button
                  className="block w-full text-left rounded-md px-3 py-2 text-base font-medium text-foreground/70 hover:bg-primary/10 hover:text-primary"
                  onClick={handleSignOut}
                >
                  Log Out
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
} 