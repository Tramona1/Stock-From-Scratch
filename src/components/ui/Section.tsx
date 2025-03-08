import React from "react"
import { cn } from "@/lib/utils"

interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  variant?: "default" | "muted" | "primary" | "grid"
  as?: React.ElementType
}

export function Section({ variant = "default", as: Component = "section", className, ...props }: SectionProps) {
  return (
    <Component
      className={cn(
        variant === "default" && "bg-background",
        variant === "muted" && "bg-muted/50",
        variant === "primary" && "bg-primary text-primary-foreground",
        variant === "grid" && "bg-gradient-to-r from-blue-50/50 to-indigo-50/50",
        "py-12 md:py-16",
        className
      )}
      {...props}
    />
  )
} 