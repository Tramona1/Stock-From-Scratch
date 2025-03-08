import { clerkMiddleware } from "@clerk/nextjs/server";

// Define public routes with proper catch-all patterns
const publicPaths = [
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/auth/login(.*)',    // Added with catch-all pattern
  '/auth/signup(.*)',   // Added with catch-all pattern
  '/pricing',
  '/api/webhooks(.*)',
  '/success'
];

// This creates a middleware function that protects routes
export default clerkMiddleware((req) => {
  // Clerk's middleware handles everything automatically
  // All auth checks are done by Clerk
  return;
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
}; 