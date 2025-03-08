import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import { Database } from '@/types/supabase';

// Create a single supabase client for interacting with your database
export const createClient = () => {
  // Check if environment variables are available at runtime
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables');
    throw new Error('Missing Supabase environment variables');
  }
  
  return createSupabaseClient<Database>(
    supabaseUrl,
    supabaseAnonKey,
    {
      auth: {
        persistSession: true,
        storageKey: 'stock-app-auth',
      },
      global: {
        headers: {
          'x-application-name': 'stock-analytics-dashboard',
        },
      },
    }
  );
};

// Initialize client in development to catch errors early
if (process.env.NODE_ENV === 'development') {
  try {
    createClient();
  } catch (error) {
    console.error('Supabase client initialization error:', error);
  }
} 