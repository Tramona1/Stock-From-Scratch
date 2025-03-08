"use client"

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
import { cn } from "@/lib/utils"
import { usePathname } from "next/navigation"

const sidebarItems = [
  { icon: Home, label: "Overview", href: "/dashboard" },
  { icon: BarChart3, label: "Hedge Funds", href: "/dashboard/hedge-funds" },
  { icon: UserCheck, label: "Insider Trading", href: "/dashboard/insider-trading" },
  { icon: DollarSign, label: "Options Flow", href: "/dashboard/options-flow" },
  { icon: LineChart, label: "Technical", href: "/dashboard/technical" },
  { icon: Bell, label: "Alerts", href: "/dashboard/alerts" },
  { icon: Settings, label: "Settings", href: "/dashboard/settings" },
]

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  return (
    <div className="flex min-h-screen">
      {/* Sidebar - fixed position with strong styling */}
      <div 
        className="fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 shadow-lg top-14 z-50"
        style={{ 
          height: 'calc(100vh - 56px)', 
          boxShadow: '4px 0 10px rgba(0, 0, 0, 0.05)' 
        }}
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold">Dashboard</h2>
        </div>
        <nav className="p-4">
          <ul className="space-y-2">
            {sidebarItems.map((item, index) => {
              const isActive = pathname === item.href;
              return (
                <li key={index}>
                  <Link 
                    href={item.href}
                    className={cn(
                      "flex items-center p-3 rounded-md group transition-colors",
                      isActive 
                        ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium" 
                        : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200"
                    )}
                  >
                    <item.icon className={cn(
                      "h-5 w-5 mr-3",
                      isActive 
                        ? "text-blue-600 dark:text-blue-400" 
                        : "text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200"
                    )} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      {/* Main content */}
      <div className="ml-64 flex-1 w-full overflow-auto">
        {children}
      </div>
    </div>
  )
} 