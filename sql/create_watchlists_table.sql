-- Create watchlists table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS watchlist_access_policy ON public.watchlists;

-- Create RLS policy to ensure users can only access their own watchlist items
CREATE POLICY watchlist_access_policy ON public.watchlists
  FOR ALL
  USING (user_id = auth.uid()::TEXT);

-- Create a unique constraint to prevent duplicate tickers for the same user
ALTER TABLE public.watchlists 
DROP CONSTRAINT IF EXISTS watchlists_user_id_ticker_key;

ALTER TABLE public.watchlists 
ADD CONSTRAINT watchlists_user_id_ticker_key UNIQUE (user_id, ticker);

-- Comment on the table
COMMENT ON TABLE public.watchlists IS 'Stores user watchlist entries - tickers that users want to track'; 