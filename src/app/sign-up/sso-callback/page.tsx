"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useClerk } from "@clerk/nextjs"
import { Loader2 } from "lucide-react"

export default function SignUpSSO() {
  const router = useRouter()
  const { handleRedirectCallback } = useClerk()

  useEffect(() => {
    // Handle the redirect callback
    handleRedirectCallback({
      redirectUrl: window.location.href,
    })
      .then(() => {
        // Clerk handles the redirect automatically
        console.log("SSO callback complete")
      })
      .catch((err) => {
        console.error("Error handling SSO callback:", err)
        router.push("/sign-in")
      })
  }, [router, handleRedirectCallback])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="text-center">
        <Loader2 className="mx-auto h-16 w-16 animate-spin text-primary" />
        <h2 className="mt-6 text-xl font-semibold">Completing your sign up...</h2>
        <p className="mt-2 text-muted-foreground">You'll be redirected shortly.</p>
      </div>
    </div>
  )
} 