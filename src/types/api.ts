// Stock Information
export interface StockInfo {
  ticker: string;
  full_name: string;
  sector: string;
  marketcap: number;
  current_price: number;
  daily_volume: number;
  change_percent: number;
  updated_at: string;
}

// Market Indicators
export interface MarketIndicator {
  id: number;
  name: string;
  value: number;
  max_value: number;
  description: string;
  updated_at: string;
}

// Insider Trading Data
export interface InsiderTrade {
  id: number;
  ticker: string;
  company_name: string;
  insider_name: string;
  insider_position: string;
  transaction_type: 'Buy' | 'Sell' | 'Option Exercise';
  transaction_date: string;
  shares: number;
  avg_price: number;
  total_value: number;
  shares_owned: number;
  filing_date: string;
}

// Hedge Fund Holdings
export interface HedgeFundHolding {
  id: number;
  fund_name: string;
  ticker: string;
  company_name: string;
  action: 'New Position' | 'Increased' | 'Decreased' | 'Sold Out';
  shares: number;
  value: number;
  change_percent: number;
  filing_date: string;
  quarter_end: string;
}

// Options Flow Data
export interface OptionsFlow {
  id: number;
  ticker: string;
  date: string;
  contract_type: 'Call' | 'Put';
  strike_price: number;
  expiration_date: string;
  premium: number;
  volume: number;
  open_interest: number;
  sentiment: 'Bullish' | 'Bearish' | 'Neutral';
  time: string;
  implied_volatility: number;
}

// Dark Pool Data
export interface DarkPoolData {
  id: number;
  ticker: string;
  volume: number;
  price: number;
  blocks_count: number;
  largest_block_size: number;
  data_date: string;
  percent_of_daily_volume: number;
}

// Watchlist Item
export interface WatchlistItem {
  id: number;
  user_id: string;
  ticker: string;
  created_at: string;
  stock_info?: StockInfo;
} 