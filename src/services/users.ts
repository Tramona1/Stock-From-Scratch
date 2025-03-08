import { supabase } from '@/lib/supabase';
import { createClient } from '@/lib/supabase/server';
import type { Database } from '../types/supabase';

export type User = Database['public']['Tables']['users']['Row'];
export type UserUpdateData = Database['public']['Tables']['users']['Update'];

/**
 * Get a user from Supabase by their ID 
 * Server-side function using the service role
 */
export async function getUserById(userId: string): Promise<User | null> {
  try {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();
    
    if (error) {
      console.error('Error fetching user:', error);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Unexpected error fetching user:', error);
    return null;
  }
}

/**
 * Update a user's profile in Supabase
 * Server-side function using the service role
 */
export async function updateUser(userId: string, userData: UserUpdateData): Promise<boolean> {
  try {
    const supabase = createClient();
    const { error } = await supabase
      .from('users')
      .update({
        ...userData,
        updated_at: new Date().toISOString()
      })
      .eq('id', userId);
    
    if (error) {
      console.error('Error updating user:', error);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Unexpected error updating user:', error);
    return false;
  }
}

/**
 * Get a user's subscription status
 * Server-side function using the service role
 */
export async function getUserSubscription(userId: string) {
  try {
    console.log(`Fetching subscription for user: ${userId}`);
    const supabase = createClient();
    const { data, error } = await supabase
      .from('users')
      .select('subscription_status, subscription_id, plan_type, is_annual, current_period_end, cancel_at_period_end')
      .eq('id', userId)
      .single();
    
    if (error) {
      console.error('Error fetching user subscription:', error);
      // Don't use mock data - log the error and return null
      return null;
    }
    
    // If no data returned, log and return null
    if (!data) {
      console.log(`No subscription data found for user: ${userId}`);
      return null;
    }
    
    // Validate currentPeriodEnd - set to null if invalid (year < 2000)
    let currentPeriodEnd = data.current_period_end;
    if (currentPeriodEnd) {
      const date = new Date(currentPeriodEnd);
      if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
        currentPeriodEnd = null;
      }
    }
    
    return {
      status: data.subscription_status,
      plan: data.plan_type,
      isAnnual: data.is_annual,
      currentPeriodEnd: currentPeriodEnd,
      cancelAtPeriodEnd: data.cancel_at_period_end,
      subscriptionId: data.subscription_id
    };
  } catch (error) {
    console.error('Unexpected error fetching user subscription:', error);
    return null;
  }
}

/**
 * Update a user's subscription status
 * Server-side function using the service role
 */
export async function updateUserSubscription(
  userId: string, 
  subscriptionData: {
    subscriptionId?: string,
    status?: string,
    plan?: string,
    isAnnual?: boolean,
    currentPeriodEnd?: string,
    cancelAtPeriodEnd?: boolean
  }
): Promise<boolean> {
  try {
    console.log(`Updating subscription for user ${userId} with data:`, JSON.stringify(subscriptionData));
    
    const supabase = createClient();
    
    // Create an update object including only the fields that are provided
    const updateData: any = {
      updated_at: new Date().toISOString()
    };
    
    if (subscriptionData.subscriptionId !== undefined) {
      updateData.subscription_id = subscriptionData.subscriptionId;
    }
    
    if (subscriptionData.status !== undefined) {
      updateData.subscription_status = subscriptionData.status;
    }
    
    if (subscriptionData.plan !== undefined) {
      updateData.plan_type = subscriptionData.plan;
    }
    
    if (subscriptionData.isAnnual !== undefined) {
      updateData.is_annual = subscriptionData.isAnnual;
    }
    
    if (subscriptionData.currentPeriodEnd !== undefined) {
      updateData.current_period_end = subscriptionData.currentPeriodEnd;
    }
    
    if (subscriptionData.cancelAtPeriodEnd !== undefined) {
      updateData.cancel_at_period_end = subscriptionData.cancelAtPeriodEnd;
    }
    
    console.log(`Updating with data:`, JSON.stringify(updateData));
    
    const { error } = await supabase
      .from('users')
      .update(updateData)
      .eq('id', userId);
    
    if (error) {
      console.error('Error updating user subscription:', error);
      return false;
    }
    
    console.log(`Subscription updated successfully for user ${userId}`);
    return true;
  } catch (error) {
    console.error('Unexpected error updating user subscription:', error);
    return false;
  }
}

/**
 * Create a new user in Supabase if they don't exist yet
 * This is a fallback mechanism when the Clerk webhook fails to create the user
 */
export async function createUserIfNotExists(userId: string, email?: string, firstName?: string, lastName?: string): Promise<boolean> {
  try {
    console.log(`Checking if user exists and creating if needed: ${userId}`);
    const supabase = createClient();
    
    // First check if the user already exists
    const { data: existingUser, error: checkError } = await supabase
      .from('users')
      .select('id')
      .eq('id', userId)
      .single();
      
    // If user already exists, nothing to do
    if (existingUser) {
      console.log(`User ${userId} already exists in Supabase`);
      return true;
    }
    
    if (checkError && checkError.code !== 'PGRST116') {
      // This is an error other than "no rows returned"
      console.error('Error checking for existing user:', checkError);
      return false;
    }
    
    // User doesn't exist, create them
    console.log(`Creating new user in Supabase: ${userId}`);
    
    const { error: insertError } = await supabase
      .from('users')
      .insert({
        id: userId,
        email: email || 'unknown@example.com',
        first_name: firstName || null,
        last_name: lastName || null,
        subscription_status: 'inactive',
        plan_type: 'free',
        is_annual: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        cancel_at_period_end: false
      });
      
    if (insertError) {
      console.error('Error creating user in Supabase:', insertError);
      return false;
    }
    
    console.log(`Successfully created user ${userId} in Supabase`);
    return true;
  } catch (error) {
    console.error('Unexpected error creating user:', error);
    return false;
  }
} 