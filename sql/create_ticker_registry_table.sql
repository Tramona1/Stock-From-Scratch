-- Create the ticker registry table to track active tickers for data collection

-- First ensure the uuid-ossp extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the ticker registry table
CREATE TABLE IF NOT EXISTS public.ticker_registry (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT TRUE,
  first_added TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  watchlist_count INTEGER DEFAULT 1,
  activation_reason TEXT,
  last_collected JSONB DEFAULT '{}'::jsonb
);

-- Add comment for documentation
COMMENT ON TABLE public.ticker_registry IS 'Tracks tickers for active data collection';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ticker_registry_ticker ON public.ticker_registry(ticker);
CREATE INDEX IF NOT EXISTS idx_ticker_registry_is_active ON public.ticker_registry(is_active);

-- Create a function to increment the watchlist count
CREATE OR REPLACE FUNCTION increment_watchlist_count(ticker_param TEXT)
RETURNS INTEGER AS $$
DECLARE
  current_count INTEGER;
BEGIN
  SELECT watchlist_count INTO current_count
  FROM public.ticker_registry
  WHERE ticker = ticker_param;
  
  RETURN current_count + 1;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get active tickers
CREATE OR REPLACE FUNCTION get_active_tickers()
RETURNS TABLE (ticker TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT tr.ticker
  FROM public.ticker_registry tr
  WHERE tr.is_active = TRUE;
END;
$$ LANGUAGE plpgsql; 