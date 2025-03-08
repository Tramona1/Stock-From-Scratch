"use client"

import React from "react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

export function FAQ() {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem 
        value="item-1" 
        trigger={<AccordionTrigger>What makes this different from other stock alert tools?</AccordionTrigger>}
      >
        <AccordionContent>
          Unlike many alert tools that only track basic price movements or news mentions, we track institutional activity—hedge funds, big banks, and corporate insiders. When Renaissance Technologies adds to their position or a CEO sells shares, you'll know immediately, not after reading about it in the news days later.
        </AccordionContent>
      </AccordionItem>
      
      <AccordionItem 
        value="item-2"
        trigger={<AccordionTrigger>Do I need to be an experienced trader to use this?</AccordionTrigger>}
      >
        <AccordionContent>
          Not at all. Our alerts are designed to be clear and actionable for investors of all experience levels. We explain what each alert means and why it might be significant, so you're never left wondering "so what?".
        </AccordionContent>
      </AccordionItem>
      
      <AccordionItem 
        value="item-3"
        trigger={<AccordionTrigger>How much does it cost?</AccordionTrigger>}
      >
        <AccordionContent>
          We offer a free tier that lets you track 3 assets with weekly summaries. Our paid plans start at $29/month for 10 assets with real-time alerts, and $79/month for unlimited tracking plus dark pool insights.
        </AccordionContent>
      </AccordionItem>
      
      <AccordionItem 
        value="item-4"
        trigger={<AccordionTrigger>How timely are the alerts?</AccordionTrigger>}
      >
        <AccordionContent>
          Our system processes market data in real-time. For events like unusual options activity or dark pool trades, you'll be notified within seconds. For SEC filings like 13F (hedge fund holdings) or Form 4 (insider trading), alerts go out within minutes of their publication.
        </AccordionContent>
      </AccordionItem>
      
      <AccordionItem 
        value="item-5"
        trigger={<AccordionTrigger>Can I customize what types of alerts I receive?</AccordionTrigger>}
      >
        <AccordionContent>
          Absolutely. You can choose to receive only specific types of alerts (e.g., only insider trading, only hedge fund activity) and set thresholds (e.g., only alert me of options trades over $250K).
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
} 