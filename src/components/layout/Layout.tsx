"use client"

import { ReactNode } from "react"
import { usePathname } from "next/navigation"

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const pathname = usePathname()
  
  // Don't render sidebar on the homepage
  const isHomePage = pathname === "/"
  
  return (
    <div className="min-h-screen flex">
      {!isHomePage && (
        <div className="w-64 bg-background border-r">
          {/* Sidebar content */}
        </div>
      )}
      <div className="flex-1">{children}</div>
    </div>
  )
} 