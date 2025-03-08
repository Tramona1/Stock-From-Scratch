"use client"

import * as React from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { TickerInput } from "@/components/TickerInput"
import { ArrowRight } from "lucide-react"

export function InterestForm() {
  const [step, setStep] = React.useState(1)
  const [email, setEmail] = React.useState("")
  const [tickers, setTickers] = React.useState<string[]>([])

  const handleTickerAdd = (ticker: string) => {
    if (!tickers.includes(ticker)) {
      setTickers([...tickers, ticker])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (step === 1 && email) {
      setStep(2)
    } else if (step === 2) {
      console.log("Form submitted:", { email, tickers })
      // Here you would submit the form data to your backend
      setStep(3)
    }
  }

  return (
    <Card className="w-full max-w-md shadow-lg border-blue-100">
      <form onSubmit={handleSubmit}>
        {step === 1 && (
          <>
            <CardHeader>
              <CardTitle className="text-xl text-blue-900">Get Started Free</CardTitle>
              <CardDescription>Enter your email to begin tracking market insights</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Input
                  type="email"
                  placeholder="Your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12"
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full">
                Continue <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </>
        )}

        {step === 2 && (
          <>
            <CardHeader>
              <CardTitle className="text-xl text-blue-900">What do you own?</CardTitle>
              <CardDescription>Add up to 3 assets to track (stocks, crypto, etc.)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <TickerInput onAdd={handleTickerAdd} />
                <div className="text-sm text-muted-foreground">
                  {tickers.length}/3 assets selected (Free tier)
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full">
                Start Tracking <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </>
        )}

        {step === 3 && (
          <>
            <CardHeader>
              <CardTitle className="text-xl text-blue-900">All Set!</CardTitle>
              <CardDescription>We've sent a confirmation to your email</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-green-100 rounded-full mx-auto flex items-center justify-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    className="w-8 h-8 text-green-600"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-muted-foreground">
                  Check your inbox for login details and get ready for institutional-grade insights!
                </p>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={() => window.location.href = "/dashboard"}>
                Go to Dashboard
              </Button>
            </CardFooter>
          </>
        )}
      </form>
    </Card>
  )
} 