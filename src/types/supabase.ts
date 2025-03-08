/**
 * Supabase database type definitions
 */
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          first_name: string | null
          last_name: string | null
          created_at: string
          updated_at: string
          subscription_status: string
          subscription_id: string | null
          stripe_customer_id: string | null
          plan_type: string
          is_annual: boolean
          current_period_end: string | null
          cancel_at_period_end: boolean | null
        }
        Insert: {
          id: string
          email: string
          first_name?: string | null
          last_name?: string | null
          created_at?: string
          updated_at?: string
          subscription_status?: string
          subscription_id?: string | null
          stripe_customer_id?: string | null
          plan_type?: string
          is_annual?: boolean
          current_period_end?: string | null
          cancel_at_period_end?: boolean | null
        }
        Update: {
          id?: string
          email?: string
          first_name?: string | null
          last_name?: string | null
          created_at?: string
          updated_at?: string
          subscription_status?: string
          subscription_id?: string | null
          stripe_customer_id?: string | null
          plan_type?: string
          is_annual?: boolean
          current_period_end?: string | null
          cancel_at_period_end?: boolean | null
        }
      }
      watchlists: {
        Row: {
          id: string
          user_id: string
          ticker: string
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          ticker: string
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          ticker?: string
          created_at?: string
        }
      }
      stock_info: {
        Row: {
          id: string
          ticker: string
          company_name: string
          sector: string
          industry: string
          market_cap: number
          price: number
          price_change_percent: number
          analyst_rating: string | null
          last_updated: string
        }
        Insert: {
          id?: string
          ticker: string
          company_name: string
          sector: string
          industry: string
          market_cap: number
          price: number
          price_change_percent: number
          analyst_rating?: string | null
          last_updated?: string
        }
        Update: {
          id?: string
          ticker?: string
          company_name?: string
          sector?: string
          industry?: string
          market_cap?: number
          price?: number
          price_change_percent?: number
          analyst_rating?: string | null
          last_updated?: string
        }
      }
      market_indicators: {
        Row: {
          id: string
          name: string
          value: number
          change_percent: number
          interpretation: string
          category: string
          last_updated: string
        }
        Insert: {
          id?: string
          name: string
          value: number
          change_percent: number
          interpretation: string
          category: string
          last_updated?: string
        }
        Update: {
          id?: string
          name?: string
          value?: number
          change_percent?: number
          interpretation?: string
          category?: string
          last_updated?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
} 