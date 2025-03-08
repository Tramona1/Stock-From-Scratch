"use client";

import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface UserData {
  preferences?: {
    darkMode: boolean;
    notifications: boolean;
  };
  settings?: any;
  id?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
}

export function useAuth() {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [userData, setUserData] = useState<UserData | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      setIsLoading(false);
      return;
    }

    async function loadUserData() {
      try {
        const response = await fetch("/api/auth/user");
        if (!response.ok) throw new Error("Failed to load user data");
        const data = await response.json();
        setUserData(data);
      } catch (error) {
        console.error("Error loading user data:", error);
      } finally {
        setIsLoading(false);
      }
    }

    loadUserData();
  }, [isLoaded, isSignedIn, user?.id]);

  const redirectToLogin = () => {
    router.push("/auth/login");
  };

  return {
    isLoaded: isLoaded && !isLoading,
    isSignedIn,
    user,
    userData,
    redirectToLogin,
  };
} 