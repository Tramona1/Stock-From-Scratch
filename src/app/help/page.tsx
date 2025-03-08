"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion"
import { Search } from "lucide-react"
import Link from "next/link"

const faqs = [
  {
    question: "How do I upgrade my subscription?",
    answer: "You can upgrade your subscription by going to the Billing page in your profile. Click on 'Manage Subscription' and select your desired plan. Your billing will be prorated and you'll gain immediate access to the new features."
  },
  {
    question: "How do I cancel my subscription?",
    answer: "To cancel your subscription, go to the Billing page in your profile and click 'Cancel Subscription'. Your subscription will remain active until the end of your current billing period. You can reactivate your subscription at any time before it expires."
  },
  {
    question: "What payment methods do you accept?",
    answer: "We accept all major credit cards (Visa, Mastercard, American Express) as well as PayPal for subscription payments."
  },
  {
    question: "How do I change my email address?",
    answer: "Your email address is managed through your Clerk account. Click on 'Security Settings' in your profile to access your Clerk account settings, where you can update your email address and manage your authentication options."
  },
  {
    question: "How do I add stocks to my watchlist?",
    answer: "To add stocks to your watchlist, navigate to the dashboard and use the search bar to find a stock by ticker or company name. Click the '+' button next to the stock to add it to your watchlist. You can view and manage your watchlist from the dashboard."
  },
  {
    question: "What market data is included in my subscription?",
    answer: "All subscription tiers include real-time stock quotes, basic technical indicators, and market news. Advanced and Pro tiers include additional features such as AI-powered analysis, advanced technical indicators, and customizable alerts."
  },
  {
    question: "Is there a mobile app available?",
    answer: "We're currently working on mobile apps for iOS and Android. In the meantime, our website is fully responsive and works great on mobile devices."
  },
  {
    question: "How do I get help if my question isn't answered here?",
    answer: "For additional support, please contact our support team at support@stockfromscratch.com or use the Contact button below to send us a message. We typically respond within 24 hours."
  }
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  
  // Filter FAQs based on search query
  const filteredFaqs = searchQuery 
    ? faqs.filter(faq => 
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) || 
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : faqs;
  
  return (
    <div className="container mx-auto py-10 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Help & Support</h1>
        <p className="text-muted-foreground mt-2">
          Find answers to frequently asked questions and get support
        </p>
      </div>
      
      <div className="grid gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Search Help Topics</CardTitle>
            <CardDescription>Find answers to your questions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search for help topics..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Frequently Asked Questions</CardTitle>
            <CardDescription>Common questions and answers</CardDescription>
          </CardHeader>
          <CardContent>
            {filteredFaqs.length > 0 ? (
              <Accordion type="single" collapsible className="w-full">
                {filteredFaqs.map((faq, index) => (
                  <AccordionItem 
                    key={index} 
                    value={`item-${index}`}
                    trigger={
                      <AccordionTrigger>{faq.question}</AccordionTrigger>
                    }
                  >
                    <AccordionContent>{faq.answer}</AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No matching questions found.</p>
                <p className="mt-2">Try a different search term or contact support.</p>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Still Need Help?</CardTitle>
            <CardDescription>Contact our support team</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              If you couldn't find an answer to your question, our support team is here to help.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button asChild variant="outline" className="flex-1">
                <a href="mailto:Blakesingleton@hotmail.com">Email Support</a>
              </Button>
              <Button asChild className="flex-1">
                <a href="mailto:Blakesingleton@hotmail.com">Contact Us</a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 