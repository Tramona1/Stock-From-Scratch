-- Drop the existing dark_pool_trades table if it exists
DROP TABLE IF EXISTS dark_pool_trades;

-- Create the dark_pool_trades table
CREATE TABLE dark_pool_trades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  executed_at timestamp with time zone,
  price numeric,
  size integer,
  premium numeric,
  volume integer,
  market_center text,
  ext_hour_sold_codes text,
  sale_cond_codes text,
  trade_code text,
  trade_settlement text,
  canceled boolean DEFAULT false,
  tracking_id text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_dark_pool_trades_ticker ON dark_pool_trades (ticker);
CREATE INDEX IF NOT EXISTS idx_dark_pool_trades_executed_at ON dark_pool_trades (executed_at);
CREATE INDEX IF NOT EXISTS idx_dark_pool_trades_premium ON dark_pool_trades (premium);
CREATE INDEX IF NOT EXISTS idx_dark_pool_trades_market_center ON dark_pool_trades (market_center);

-- Enable Row Level Security
ALTER TABLE dark_pool_trades ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY dark_pool_trades_select_policy ON dark_pool_trades
    FOR SELECT USING (true);

CREATE POLICY dark_pool_trades_insert_policy ON dark_pool_trades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY dark_pool_trades_update_policy ON dark_pool_trades
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Set up trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_dark_pool_trades_updated_at
BEFORE UPDATE ON dark_pool_trades
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 