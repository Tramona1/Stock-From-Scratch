"use client"

import * as React from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface FeatureCardProps {
  title: string
  description: string
  tagline?: string
  icon: React.ReactNode
  href?: string
  buttonText?: string
}

export function FeatureCard({
  title,
  description,
  tagline,
  icon,
  href = "#",
  buttonText = "Learn more",
}: FeatureCardProps) {
  return (
    <Card className="transition-all duration-300 hover:shadow-md">
      <CardHeader>
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
          {icon}
        </div>
        <CardTitle>{title}</CardTitle>
        {tagline && <CardDescription className="text-base">{tagline}</CardDescription>}
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Link href={href} passHref>
          <Button variant="outline">{buttonText}</Button>
        </Link>
      </CardContent>
    </Card>
  )
} 