"use client"

import { SignUp } from "@clerk/nextjs"

export default function Page() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-6 bg-white shadow-md rounded-lg">
        <SignUp />
      </div>
    </div>
  )
}

export const dynamic = 'force-dynamic';