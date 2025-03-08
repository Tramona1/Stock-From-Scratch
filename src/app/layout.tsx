import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ClerkProvider } from '@clerk/nextjs'
import Script from 'next/script'
import { Header } from '@/components/layout/Header'
import { Toaster } from "@/components/ui/toaster"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Stock Analytics Dashboard",
  description: "AI-powered stock analytics and market intelligence",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/dashboard"
      afterSignUpUrl="/dashboard"
    >
      <html lang="en">
        <body className={inter.className}>
          <Header />
          {children}
          <Toaster />
          
          <Script id="remove-sidebar" strategy="afterInteractive">
            {`
              function removeSidebar() {
                // Never touch auth-buttons
                const authButtonsEl = document.getElementById('auth-buttons');
                
                // More selective targeting for the sidebar only
                document.querySelectorAll('body > div > div > div').forEach(el => {
                  if (!el || !el.textContent) return;
                  
                  // Never touch the header or auth elements
                  if (
                    el.querySelector('header') || 
                    el.closest('header') ||
                    el.getAttribute('role') === 'banner' ||
                    el.className.includes('header') ||
                    el === authButtonsEl ||
                    el.contains(authButtonsEl) || 
                    el.closest('#auth-buttons') ||
                    el.querySelector('[data-clerk-signin]') ||
                    el.closest('[data-clerk-signin]') ||
                    el.querySelector('[class*="clerk"]') ||
                    el.closest('[class*="clerk"]')
                  ) {
                    return;
                  }
                  
                  const text = el.textContent.trim();
                  // Only match the sidebar three items specifically
                  if (
                    (text === 'DashboardAnalysisPortfolio' || 
                     text === 'Dashboard\\nAnalysis\\nPortfolio' ||
                     (text.includes('Dashboard') && 
                      text.includes('Analysis') && 
                      text.includes('Portfolio') && 
                      !text.includes('Sign') &&
                      !text.includes('Up') &&
                      !text.includes('Login') &&
                      !text.includes('In') &&
                      text.split(/\\s+/).length <= 5)
                    )
                  ) {
                    el.style.display = 'none';
                  }
                });
              }
              
              // Wait for the page to be fully loaded
              if (document.readyState === 'complete') {
                removeSidebar();
              } else {
                window.addEventListener('load', function() {
                  setTimeout(removeSidebar, 300);
                });
              }
            `}
          </Script>
        </body>
      </html>
    </ClerkProvider>
  )
} 