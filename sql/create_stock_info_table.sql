-- Drop the existing stock_info table if it exists
DROP TABLE IF EXISTS stock_info;

-- Create the stock_info table
CREATE TABLE stock_info (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL UNIQUE,
  company_name text,
  sector text,
  industry text,
  exchange text,
  market_cap numeric,
  shares_outstanding numeric,
  float numeric,
  current_price numeric,
  open_price numeric,
  daily_high numeric,
  daily_low numeric,
  daily_volume numeric,
  fifty_two_week_high numeric,
  fifty_two_week_low numeric,
  pe_ratio numeric,
  eps numeric,
  dividend_yield numeric,
  beta numeric,
  avg_volume numeric,
  description text,
  company_website text,
  headquarters text,
  logo_url text,
  ceo text,
  employees integer,
  founded_year integer,
  market_time text,
  price_updated_at timestamp with time zone,
  fetched_at timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_stock_info_ticker ON stock_info (ticker);
CREATE INDEX IF NOT EXISTS idx_stock_info_sector ON stock_info (sector);
CREATE INDEX IF NOT EXISTS idx_stock_info_industry ON stock_info (industry);
CREATE INDEX IF NOT EXISTS idx_stock_info_fetched_at ON stock_info (fetched_at);

-- Enable Row Level Security
ALTER TABLE stock_info ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY stock_info_select_policy ON stock_info
    FOR SELECT USING (true);

CREATE POLICY stock_info_insert_policy ON stock_info
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY stock_info_update_policy ON stock_info
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at column
CREATE TRIGGER update_stock_info_updated_at
BEFORE UPDATE ON stock_info
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 