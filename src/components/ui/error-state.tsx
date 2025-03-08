import * as React from "react"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertCircle, RefreshCw } from "lucide-react"

interface ErrorStateProps {
  title: string
  description?: string
  error?: unknown
  showDetails?: boolean
  showRefresh?: boolean
  onAction?: () => void
  actionText?: string
}

export function ErrorState({
  title,
  description,
  error,
  showDetails = false,
  showRefresh = true,
  onAction,
  actionText = "Retry"
}: ErrorStateProps) {
  // Convert error to a string representation for display
  const errorMessage = error instanceof Error ? error.message : 
                      typeof error === 'string' ? error : 
                      error ? JSON.stringify(error) : '';

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{description}</p>
        
        {showDetails && errorMessage && (
          <div className="mt-4 p-2 bg-muted/50 rounded-md text-xs font-mono overflow-auto max-h-32">
            {errorMessage}
          </div>
        )}
      </CardContent>
      <CardFooter>
        {showRefresh && onAction && (
          <Button variant="outline" onClick={onAction} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            {actionText}
          </Button>
        )}
      </CardFooter>
    </Card>
  )
} 