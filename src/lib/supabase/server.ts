import { createClient as createClientBase } from '@supabase/supabase-js';
import type { Database } from '../../types/supabase';

// Cache the Supabase client to avoid creating a new client for every call
let supabaseClient: ReturnType<typeof createClientBase<Database>> | null = null;

/**
 * Creates a Supabase client with the service role key for server operations
 * This gives full access to the database, so it should only be used in server contexts
 */
export function createClient() {
  // Return the cached client if it exists
  if (supabaseClient) {
    return supabaseClient;
  }
  
  // Check environment variables
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  // If we're in development and missing the service role key but have the anon key,
  // use that as a fallback with a warning
  const isDev = process.env.NODE_ENV === 'development';
  
  if (!supabaseUrl) {
    console.error('Missing Supabase URL');
    if (isDev) {
      return createMockClient();
    }
    throw new Error('Missing Supabase URL');
  }
  
  if (!supabaseKey) {
    console.warn('Missing SUPABASE_SERVICE_ROLE_KEY - using fallback in development mode');
    if (isDev) {
      // In development, use the anon key if available as fallback
      const fallbackKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
      if (fallbackKey) {
        console.info('Using NEXT_PUBLIC_SUPABASE_ANON_KEY as fallback for development');
        supabaseClient = createClientBase<Database>(supabaseUrl, fallbackKey, {
          auth: {
            persistSession: false,
            autoRefreshToken: false,
          },
        });
        return supabaseClient;
      }
      
      return createMockClient();
    }
    
    throw new Error('Missing SUPABASE_SERVICE_ROLE_KEY environment variable');
  }
  
  // Create a new client with the service role key
  supabaseClient = createClientBase<Database>(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false, // No need to persist sessions in server contexts
      autoRefreshToken: false,
    },
  });
  
  return supabaseClient;
}

/**
 * Creates a mock Supabase client for development when keys aren't available
 * This allows the application to run without a real Supabase connection
 */
function createMockClient() {
  console.info('Creating mock Supabase client for development');
  // Return a mocked client that doesn't throw errors
  return {
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: null, error: null }),
          execute: async () => ({ data: [], error: null }),
        }),
        execute: async () => ({ data: [], error: null }),
      }),
      insert: async () => ({ data: null, error: null }),
      update: async () => ({ data: null, error: null }),
      delete: async () => ({ data: null, error: null }),
    }),
  } as any;
}

/**
 * Helper function to create a client for a specific user with their auth token
 * This is useful for operations that should be performed with the user's permissions
 */
export function createClientWithAuth(supabaseAccessToken: string) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables');
    if (process.env.NODE_ENV === 'development') {
      return createMockClient();
    }
    throw new Error('Missing Supabase environment variables');
  }
  
  return createClientBase<Database>(supabaseUrl, supabaseAnonKey, {
    global: {
      headers: {
        Authorization: `Bearer ${supabaseAccessToken}`,
      },
    },
    auth: {
      persistSession: false,
    },
  });
} 