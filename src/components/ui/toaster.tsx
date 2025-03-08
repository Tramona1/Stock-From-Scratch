"use client"

import { useToast } from '@/components/ui/use-toast'
import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle } from 'lucide-react'

export function Toaster() {
  const { toasts } = useToast()
  
  return (
    <div className="fixed bottom-0 right-0 z-50 flex flex-col gap-2 p-4 md:max-w-[420px]">
      {toasts.map((toast, index) => (
        <Toast key={index} {...toast} />
      ))}
    </div>
  )
}

function Toast({ title, description, variant = 'default' }: {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
}) {
  const [visible, setVisible] = useState(true)
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
    }, 4500) // Slightly shorter than the removal time
    
    return () => clearTimeout(timer)
  }, [])
  
  if (!visible) return null
  
  return (
    <div 
      className={`
        relative flex items-start gap-3 rounded-md border p-4 pr-8 shadow-lg transition-all
        ${variant === 'destructive' 
          ? 'border-red-200 bg-red-50 text-red-800' 
          : 'border-gray-200 bg-white text-gray-800'
        }
      `}
    >
      <div className="flex-shrink-0 pt-0.5">
        {variant === 'destructive' ? (
          <AlertCircle className="h-5 w-5 text-red-500" />
        ) : (
          <CheckCircle className="h-5 w-5 text-green-500" />
        )}
      </div>
      <div className="flex-1">
        {title && <h5 className="mb-1 font-medium">{title}</h5>}
        {description && <div className="text-sm">{description}</div>}
      </div>
      <button 
        onClick={() => setVisible(false)}
        className="absolute right-2 top-2 rounded-md p-1 text-gray-400 hover:text-gray-600"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
} 