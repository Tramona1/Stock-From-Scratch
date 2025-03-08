export function ChartFallback({ height = 350 }: { height?: number }) {
  return (
    <div 
      className="flex items-center justify-center bg-gray-50 rounded-md border border-gray-100"
      style={{ height: `${height}px` }}
    >
      <div className="text-sm text-muted-foreground">
        Loading chart...
      </div>
    </div>
  )
} 