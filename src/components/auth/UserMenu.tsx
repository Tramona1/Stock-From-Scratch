"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";

export function UserMenu() {
  const { user, isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center animate-pulse">
        <span className="sr-only">Loading user</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link href="/dashboard/settings" passHref>
        <Button variant="ghost" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </Link>
      <UserButton
        appearance={{
          elements: {
            userButtonAvatarBox: "h-10 w-10 rounded-full bg-primary text-primary-foreground",
          },
        }}
        afterSignOutUrl="/"
      />
    </div>
  );
} 