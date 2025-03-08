import { Button } from "@/components/ui/button"
import { Container } from "@/components/ui/Container"
import { Section } from "@/components/ui/Section"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MarketTicker } from "@/components/MarketTicker"
import { AlertTicker } from "@/components/AlertTicker"
import { InterestForm } from "@/components/InterestForm"
import { FeatureCard } from "@/components/FeatureCard"
import { FAQ } from "@/components/FAQ"
import { Footer } from "@/components/Footer"
import { ArrowRight, BarChart3, Bell, Eye, Zap, Shield, Clock } from "lucide-react"
import Link from "next/link"
import { Header } from "@/components/layout/Header"
import { SidebarRemover } from './_components/SidebarRemover'

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col" data-home-page="true">
      <Header />
      <SidebarRemover />
      {/* Ticker Tape */}
      <>
        <MarketTicker />
        <AlertTicker />
      </>

      {/* Hero Section */}
      <Section variant="grid" className="overflow-hidden">
        <Container className="py-20 md:py-32">
          <div className="grid gap-12 md:grid-cols-2 md:gap-16">
            <div className="flex flex-col justify-center space-y-6">
              <Badge variant="secondary" className="w-fit">
                Stay Informed About What You Own—For Free
              </Badge>

              <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-5xl lg:text-6xl">
                Get the
                <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent animate-gradient">
                  {" "}
                  Same Insights
                </span>{" "}
                as Hedge Funds
              </h1>

              <p className="text-muted-foreground text-lg md:text-xl">
                Own a stock, some crypto, or even real estate? Sign up for our free tier and stay in the know. Big banks
                and hedge funds have long had the upper hand with elite insights—until now. We're leveling the playing
                field.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mt-8">
                <Button asChild size="lg" className="gap-2">
                  <Link href="/checkout?plan=pro&billing=monthly">
                    <ArrowRight className="h-4 w-4" />
                    Pay Now
                  </Link>
                </Button>
                <Button variant="outline" size="lg" asChild>
                  <Link href="/pricing">
                    View Pricing
                  </Link>
                </Button>
              </div>
            </div>

            <div className="relative flex items-center justify-center">
              <div className="absolute animate-pulse bg-blue-500/20 rounded-full w-64 h-64 blur-3xl"></div>
              <InterestForm />
            </div>
          </div>
        </Container>
      </Section>

      {/* Features Section */}
      <Section className="bg-gradient-to-b from-blue-50 to-white py-20">
        <Container>
          <div className="text-center mb-20">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-blue-900">
              Your Edge in the Market
            </h2>
            <p className="mt-4 text-xl text-blue-700/80 max-w-2xl mx-auto">
              Our AI digs into market data, SEC filings, and more to bring you institutional-grade insights—fast. Click
              'Learn More' to see how each feature works.
            </p>
          </div>

          <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<BarChart3 className="h-8 w-8 text-blue-600" />}
              title="Real-time Analysis"
              tagline="Track hedge fund moves, insider trades, and market sentiment as it happens."
              description="Our AI scans SEC filings, verified X posts from market influencers, and live data to flag big moves—like a hedge fund doubling its stake—that could affect your assets."
            />
            <FeatureCard
              icon={<Bell className="h-8 w-8 text-blue-600" />}
              title="Personalized Alerts"
              tagline="Get instant notifications tailored to what you own or watch."
              description="Set it up your way: 'Alert me if TSLA drops 5%' or 'Notify me of insider sales in VNQ.' You'll know the second something big happens."
            />
            <FeatureCard
              icon={<Eye className="h-8 w-8 text-blue-600" />}
              title="Dark Pool Insights"
              tagline="Spot hidden institutional trades before they hit the market."
              description="See large trades—like $1M+ in dark pools—that signal where the big money's heading."
            />
            <FeatureCard
              icon={<Zap className="h-8 w-8 text-blue-600" />}
              title="Option Flow Analysis"
              tagline="Catch bullish or bearish trends in options activity."
              description="We track hefty options trades (e.g., $100K+ premiums) to clue you in on potential price swings."
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8 text-blue-600" />}
              title="Lightning Fast"
              tagline="Alerts hit your inbox or phone within seconds."
              description="No delays—our system processes events in real-time so you're never behind."
            />
            <FeatureCard
              icon={<Clock className="h-8 w-8 text-blue-600" />}
              title="Weekly Summaries"
              tagline="A Monday recap of what moved your markets."
              description="Get a digest of last week's key activity—insider trades, hedge fund shifts, and more—tailored to your picks."
            />
          </div>
        </Container>
      </Section>

      {/* Pricing Section Preview */}
      <Section variant="muted">
        <Container className="py-16">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Simple, Transparent Pricing</h2>
            <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
              Choose the plan that fits your trading style
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 max-w-4xl mx-auto">
            <Card className="relative h-full border-primary">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-sm font-medium text-primary-foreground">
                Start Free
              </div>
              <CardHeader>
                <CardTitle>Free</CardTitle>
                <div className="mt-4 text-4xl font-bold">$0/mo</div>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-4">
                  <li className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-primary" /> Track 3 assets
                  </li>
                  <li className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-primary" /> Weekly summaries
                  </li>
                </ul>
                <Button className="mt-8 w-full">Get Started</Button>
              </CardContent>
            </Card>

            <Card className="relative h-full">
              <CardHeader>
                <CardTitle>Basic</CardTitle>
                <div className="mt-4 text-4xl font-bold">$29/mo</div>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-4">
                  <li className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-primary" /> Track 10 assets
                  </li>
                  <li className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-primary" /> Real-time alerts
                  </li>
                </ul>
                <Button className="mt-8 w-full">Get Started</Button>
              </CardContent>
            </Card>

            <Card className="relative h-full">
              <CardHeader>
                <CardTitle>Pro</CardTitle>
                <div className="mt-4 text-4xl font-bold">$79/mo</div>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-4">
                  <li className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-primary" /> Unlimited tracking
                  </li>
                  <li className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-primary" /> Dark pool insights
                  </li>
                </ul>
                <Button className="mt-8 w-full">Get Started</Button>
              </CardContent>
            </Card>
          </div>
        </Container>
      </Section>

      {/* FAQ Section */}
      <Section>
        <Container className="py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to know about our service
            </p>
          </div>
          <div className="max-w-3xl mx-auto">
            <FAQ />
          </div>
        </Container>
      </Section>

      {/* Footer */}
      <Footer />
    </div>
  )
} 