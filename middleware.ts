import { NextResponse } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';

// Define all public routes
const publicRoutes = [
  "/", 
  "/auth/login", 
  "/auth/signup", 
  "/api/public(.*)",
  "/sign-in(.*)", 
  "/sign-up(.*)",
  "/pricing"
];

export function middleware(req: NextRequest) {
  const { userId } = getAuth(req);
  const path = req.nextUrl.pathname;

  // Check if path is public
  if (publicRoutes.some(route => {
    if (route.endsWith("(.*)")) {
      const baseRoute = route.replace("(.*)", "");
      return path.startsWith(baseRoute);
    }
    return path === route || path.startsWith(route);
  })) {
    return NextResponse.next();
  }

  // If not public and no user, redirect to login
  if (!userId) {
    return NextResponse.redirect(new URL('/sign-in', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
}; 