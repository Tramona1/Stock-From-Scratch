"use client"

// Simplified toast implementation
import * as React from "react"
import { useState, useEffect } from 'react'

type ToastVariant = 'default' | 'destructive'

interface ToastProps {
  title?: string
  description?: string
  variant?: ToastVariant
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

// Simple in-memory store for toasts
let toasts: ToastProps[] = []
let listeners: ((toasts: ToastProps[]) => void)[] = []

// Helper to notify listeners when toasts change
const notifyListeners = () => {
  listeners.forEach(listener => listener([...toasts]))
}

// Function to add a toast
export function toast(props: ToastProps) {
  toasts = [...toasts, props]
  notifyListeners()
  
  // Auto-remove toast after 5 seconds
  setTimeout(() => {
    toasts = toasts.filter(t => t !== props)
    notifyListeners()
  }, 5000)
}

// Hook to access toasts
export function useToast() {
  const [toastList, setToastList] = useState<ToastProps[]>(toasts)
  
  useEffect(() => {
    // Add listener
    listeners.push(setToastList)
    
    // Remove listener on cleanup
    return () => {
      listeners = listeners.filter(l => l !== setToastList)
    }
  }, [])
  
  return {
    toasts: toastList,
    toast
  }
}

// Export types
export type { ToastProps }
export type ToastActionElement = React.ReactElement 