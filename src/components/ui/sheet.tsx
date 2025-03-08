"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

const Sheet = ({ children }: { children: React.ReactNode }) => {
  return <div>{children}</div>
}

interface SheetTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const SheetTrigger = ({ children, asChild, ...props }: SheetTriggerProps) => {
  if (asChild) {
    return <>{children}</>
  }
  
  return <button {...props}>{children}</button>
}

interface SheetContentProps extends React.HTMLAttributes<HTMLDivElement> {
  side?: 'top' | 'right' | 'bottom' | 'left'
}

const SheetContent = React.forwardRef<HTMLDivElement, SheetContentProps>(
  ({ className, children, side = 'right', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "fixed bg-background shadow-lg p-6 z-50",
        side === 'right' && "top-0 right-0 h-full w-[300px]",
        side === 'left' && "top-0 left-0 h-full w-[300px]",
        side === 'top' && "top-0 left-0 w-full h-[300px]",
        side === 'bottom' && "bottom-0 left-0 w-full h-[300px]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
SheetContent.displayName = "SheetContent"

export { Sheet, SheetTrigger, SheetContent } 