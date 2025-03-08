import { supabase } from '@/lib/supabase';
import { createClient } from '@/lib/supabase/server';
import { 
  StockInfo, 
  InsiderTrade, 
  OptionsFlow, 
  HedgeFundHolding,
  DarkPoolData,
  MarketIndicator,
  WatchlistItem
} from '@/types/api';

// ======== Stock Info ========
export async function getStocks(): Promise<StockInfo[]> {
  const { data, error } = await supabase
    .from('stock_info')
    .select('*');
  
  if (error) throw error;
  return data || [];
}

export async function getStockById(ticker: string): Promise<StockInfo | null> {
  const { data, error } = await supabase
    .from('stock_info')
    .select('*')
    .eq('ticker', ticker)
    .single();
  
  if (error) throw error;
  return data;
}

// ======== Insider Trading ========
export async function getInsiderTrades(limit: number = 10): Promise<InsiderTrade[]> {
  const { data, error } = await supabase
    .from('insider_trades')
    .select('*')
    .order('transaction_date', { ascending: false })
    .limit(limit);
  
  if (error) throw error;
  return data || [];
}

// ======== Hedge Fund Holdings ========
export async function getHedgeFundHoldings(limit: number = 10): Promise<HedgeFundHolding[]> {
  const { data, error } = await supabase
    .from('hedge_fund_holdings')
    .select('*')
    .order('filing_date', { ascending: false })
    .limit(limit);
  
  if (error) throw error;
  return data || [];
}

// ======== Options Flow ========
export async function getOptionsFlowData(limit: number = 10): Promise<OptionsFlow[]> {
  const { data, error } = await supabase
    .from('option_flow_data')
    .select('*')
    .order('date', { ascending: false })
    .limit(limit);
  
  if (error) throw error;
  return data || [];
}

// ======== Dark Pool Data ========
export async function getDarkPoolActivity(limit: number = 10): Promise<DarkPoolData[]> {
  const { data, error } = await supabase
    .from('dark_pool_data')
    .select('*')
    .order('data_date', { ascending: false })
    .limit(limit);
  
  if (error) throw error;
  return data || [];
}

// ======== Market Indicators ========
export async function getMarketIndicators(): Promise<MarketIndicator[]> {
  const { data, error } = await supabase
    .from('market_indicators')
    .select('*');
  
  if (error) throw error;
  return data || [];
}

// ======== User Watchlist ========
export async function getUserWatchlist(userId: string): Promise<WatchlistItem[]> {
  // For reading watchlist items, we can use the server client to bypass RLS
  const supabaseServer = createClient();
  const { data, error } = await supabaseServer
    .from('watchlists')
    .select('*')
    .eq('user_id', userId);
  
  if (error) throw error;
  return data || [];
}

export async function addToWatchlist(userId: string, ticker: string): Promise<void> {
  // Use server client to bypass RLS for inserting
  const supabaseServer = createClient();
  const { error } = await supabaseServer
    .from('watchlists')
    .insert({ user_id: userId, ticker });
  
  if (error) throw error;
}

export async function removeFromWatchlist(userId: string, ticker: string): Promise<void> {
  // Use server client to bypass RLS for deleting
  const supabaseServer = createClient();
  const { error } = await supabaseServer
    .from('watchlists')
    .delete()
    .eq('user_id', userId)
    .eq('ticker', ticker);
  
  if (error) throw error;
} 