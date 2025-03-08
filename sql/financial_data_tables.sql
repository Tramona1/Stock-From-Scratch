-- Create extension for UUID generation if it doesn't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Analyst Ratings Table
CREATE TABLE IF NOT EXISTS public.analyst_ratings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol TEXT NOT NULL,
  company_name TEXT,
  firm TEXT NOT NULL,
  analyst TEXT,
  rating_date DATE NOT NULL,
  old_rating TEXT,
  new_rating TEXT,
  rating_change TEXT NOT NULL,
  old_price_target DECIMAL(10, 2),
  new_price_target DECIMAL(10, 2),
  price_target_change_percent DECIMAL(5, 2),
  current_price DECIMAL(10, 2),
  sector TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS idx_analyst_ratings_symbol ON public.analyst_ratings(symbol);
CREATE INDEX IF NOT EXISTS idx_analyst_ratings_date ON public.analyst_ratings(rating_date);

-- Economic Calendar Events Table
CREATE TABLE IF NOT EXISTS public.economic_calendar_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_name TEXT NOT NULL,
  event_time TIMESTAMP WITH TIME ZONE,
  event_type TEXT,
  forecast TEXT,
  previous_value TEXT,
  reported_period TEXT,
  actual_value TEXT,
  impact TEXT,
  relevance_score INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(event_name, event_time)
);

-- FDA Calendar Events Table
CREATE TABLE IF NOT EXISTS public.fda_calendar_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT,
  drug TEXT NOT NULL,
  catalyst TEXT NOT NULL,
  description TEXT,
  indication TEXT,
  start_date DATE,
  end_date DATE,
  status TEXT,
  outcome TEXT,
  outcome_brief TEXT,
  notes TEXT,
  source_link TEXT,
  marketcap BIGINT,
  has_options BOOLEAN,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(ticker, drug, end_date)
);

CREATE INDEX IF NOT EXISTS idx_fda_calendar_ticker ON public.fda_calendar_events(ticker);
CREATE INDEX IF NOT EXISTS idx_fda_calendar_end_date ON public.fda_calendar_events(end_date);

-- Insider Trades Table
CREATE TABLE IF NOT EXISTS public.insider_trades (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  filing_id TEXT,
  symbol TEXT NOT NULL,
  company_name TEXT,
  insider_name TEXT NOT NULL,
  insider_title TEXT,
  transaction_type TEXT NOT NULL,
  transaction_date DATE NOT NULL,
  shares INTEGER,
  price DECIMAL(10, 2),
  total_value DECIMAL(14, 2),
  shares_owned_after INTEGER,
  filing_date DATE,
  source TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_insider_trades_symbol ON public.insider_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_insider_trades_date ON public.insider_trades(transaction_date);

-- Political Trades Table
CREATE TABLE IF NOT EXISTS public.political_trades (
  id TEXT PRIMARY KEY,
  politician_name TEXT NOT NULL,
  symbol TEXT,
  asset_description TEXT,
  transaction_date DATE NOT NULL,
  filing_date DATE,
  transaction_type TEXT NOT NULL,
  amount_min DECIMAL(14, 2),
  amount_max DECIMAL(14, 2),
  amount DECIMAL(14, 2),
  comment TEXT,
  party TEXT,
  state TEXT,
  district TEXT,
  chamber TEXT,
  source TEXT,
  source_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_political_trades_symbol ON public.political_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_political_trades_date ON public.political_trades(transaction_date);

-- Financial News Table
CREATE TABLE IF NOT EXISTS public.financial_news (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  source TEXT,
  content TEXT,
  summary TEXT,
  publish_date TIMESTAMP WITH TIME ZONE,
  sentiment DECIMAL(4, 2),
  symbols JSONB, -- Array of ticker symbols mentioned
  topics JSONB, -- Array of topics covered
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_financial_news_publish_date ON public.financial_news(publish_date);
CREATE INDEX IF NOT EXISTS idx_financial_news_symbols ON public.financial_news USING GIN (symbols);

-- Dark Pool Data Table
CREATE TABLE IF NOT EXISTS public.dark_pool_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT NOT NULL,
  executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  price DECIMAL(10, 2),
  size INTEGER,
  premium DECIMAL(14, 2),
  volume INTEGER,
  market_center TEXT,
  ext_hour_sold_codes TEXT,
  sale_cond_codes TEXT,
  trade_code TEXT,
  trade_settlement TEXT,
  canceled BOOLEAN DEFAULT FALSE,
  tracking_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dark_pool_ticker ON public.dark_pool_data(ticker);
CREATE INDEX IF NOT EXISTS idx_dark_pool_executed_at ON public.dark_pool_data(executed_at);

-- Options Flow Table
CREATE TABLE IF NOT EXISTS public.options_flow (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker TEXT NOT NULL,
  date TIMESTAMP WITH TIME ZONE NOT NULL,
  contract_id TEXT,
  strike_price DECIMAL(10, 2) NOT NULL,
  expiration_date DATE NOT NULL,
  option_type TEXT NOT NULL, -- 'call' or 'put'
  sentiment TEXT,
  volume INTEGER,
  open_interest INTEGER,
  implied_volatility DECIMAL(6, 2),
  premium DECIMAL(14, 2),
  unusual_score DECIMAL(5, 2),
  trade_type TEXT,
  raw_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_flow_ticker ON public.options_flow(ticker);
CREATE INDEX IF NOT EXISTS idx_options_flow_date ON public.options_flow(date);
CREATE INDEX IF NOT EXISTS idx_options_flow_expiration ON public.options_flow(expiration_date);

-- Create alert notifications table
CREATE TABLE IF NOT EXISTS public.alerts (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  type TEXT NOT NULL,
  subtype TEXT,
  importance TEXT NOT NULL, -- high, medium, low
  related_ticker TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  event_date DATE,
  days_until INTEGER,
  meta JSONB,
  is_read BOOLEAN DEFAULT FALSE,
  user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
  dismissed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_ticker ON public.alerts(user_id, related_ticker);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON public.alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON public.alerts(is_read);

-- Add Row Level Security for all tables
ALTER TABLE public.analyst_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.economic_calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fda_calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insider_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.political_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dark_pool_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.options_flow ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

-- Create policies to allow authenticated users to read data
CREATE POLICY "Allow authenticated users to read data" 
ON public.analyst_ratings FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.economic_calendar_events FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.fda_calendar_events FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.insider_trades FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.political_trades FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.financial_news FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.dark_pool_data FOR SELECT 
TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read data" 
ON public.options_flow FOR SELECT 
TO authenticated USING (true);

-- Allow users to read and update their own alerts
CREATE POLICY "Allow users to read their own alerts" 
ON public.alerts FOR SELECT 
TO authenticated USING (user_id = auth.uid()::TEXT);

CREATE POLICY "Allow users to update their own alerts" 
ON public.alerts FOR UPDATE 
TO authenticated USING (user_id = auth.uid()::TEXT);

-- Comment on tables for documentation
COMMENT ON TABLE public.analyst_ratings IS 'Stores stock analyst ratings and price target changes';
COMMENT ON TABLE public.economic_calendar_events IS 'Stores economic calendar events like Fed meetings, CPI releases, etc.';
COMMENT ON TABLE public.fda_calendar_events IS 'Stores FDA calendar events for pharmaceutical companies';
COMMENT ON TABLE public.insider_trades IS 'Stores insider trading data for company executives';
COMMENT ON TABLE public.political_trades IS 'Stores trading data for members of Congress and other politicians';
COMMENT ON TABLE public.financial_news IS 'Stores financial news articles with sentiment analysis';
COMMENT ON TABLE public.dark_pool_data IS 'Stores dark pool trading activity';
COMMENT ON TABLE public.options_flow IS 'Stores options flow data with unusual activity';
COMMENT ON TABLE public.alerts IS 'Stores user-specific alerts based on market events'; 