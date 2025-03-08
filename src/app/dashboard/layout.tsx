"use client"

import React from "react"
import { Header } from "@/components/layout/Header"
import { AuthGuard } from "@/components/auth/AuthGuard"
import { MockDataProvider } from './_components/MockDataProvider'
import { 
  Home, 
  BarChart3, 
  UserCheck, 
  DollarSign, 
  LineChart, 
  Bell,
  Settings
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { WatchlistProvider } from "@/context/WatchlistContext"

// Sidebar items definition
const sidebarItems = [
  { 
    name: "Overview", 
    href: "/dashboard", 
    icon: Home 
  },
  { 
    name: "Hedge Funds", 
    href: "/dashboard/hedge-funds", 
    icon: BarChart3 
  },
  { 
    name: "Insider Trading", 
    href: "/dashboard/insider-trading", 
    icon: UserCheck 
  },
  {
    name: "Analyst Ratings",
    href: "/dashboard/analyst-ratings",
    icon: BarChart3
  },
  { 
    name: "Options Flow", 
    href: "/dashboard/options-flow", 
    icon: DollarSign 
  },
  { 
    name: "Technical", 
    href: "/dashboard/technical", 
    icon: LineChart 
  },
  { 
    name: "Alerts", 
    href: "/dashboard/alerts", 
    icon: Bell 
  },
  { 
    name: "Settings", 
    href: "/dashboard/settings", 
    icon: Settings 
  }
]

export default function DashboardRootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <AuthGuard>
      <MockDataProvider>
        <WatchlistProvider>
          <Header />
          <div className="flex min-h-[calc(100vh-64px)]">
            {/* Sidebar */}
            <aside className="w-64 bg-background border-r border-border">
              <div className="p-4">
                <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
                <nav className="space-y-1">
                  {sidebarItems.map((item) => (
                    <Link 
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors",
                        pathname === item.href 
                          ? "bg-primary/10 text-primary font-medium" 
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                    >
                      <item.icon className="h-5 w-5" />
                      <span>{item.name}</span>
                    </Link>
                  ))}
                </nav>
              </div>
            </aside>
            
            {/* Main content */}
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </WatchlistProvider>
      </MockDataProvider>
    </AuthGuard>
  )
} 