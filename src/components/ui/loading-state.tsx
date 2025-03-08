import React from "react"
import { cn } from "@/lib/utils"

interface LoadingStateProps {
  variant?: "spinner" | "dots" | "skeleton"
  className?: string
}

export function LoadingState({ variant = "spinner", className }: LoadingStateProps) {
  if (variant === "spinner") {
    return (
      <div className={cn("flex justify-center items-center", className)}>
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-solid border-primary border-t-transparent"></div>
      </div>
    )
  }

  if (variant === "dots") {
    return (
      <div className={cn("flex justify-center items-center space-x-2", className)}>
        <div className="h-2 w-2 animate-pulse rounded-full bg-primary"></div>
        <div className="h-2 w-2 animate-pulse rounded-full bg-primary animation-delay-200"></div>
        <div className="h-2 w-2 animate-pulse rounded-full bg-primary animation-delay-400"></div>
      </div>
    )
  }

  // Skeleton variant
  return (
    <div className={cn("rounded-md bg-muted/50 animate-pulse", className || "h-40")}></div>
  )
} 