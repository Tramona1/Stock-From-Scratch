import React from "react"
import { LoadingState } from "@/components/ui/loading-state"
import { Container } from "@/components/ui/Container"

export default function DashboardLoading() {
  return (
    <div className="p-6">
      <Container>
        <div className="flex flex-col gap-8">
          <LoadingState variant="skeleton" className="max-w-4xl" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <LoadingState variant="skeleton" />
            <LoadingState variant="skeleton" />
            <LoadingState variant="skeleton" />
          </div>
          <LoadingState variant="skeleton" className="h-[400px]" />
        </div>
      </Container>
    </div>
  )
} 