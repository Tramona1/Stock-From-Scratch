-- Drop the existing political_trades table if it exists
DROP TABLE IF EXISTS political_trades;

-- Create the political_trades table
CREATE TABLE political_trades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  politician_name text,
  politician_type text,
  party text,
  state text,
  district text,
  symbol text,
  company_name text,
  transaction_date date,
  transaction_type text,
  asset_type text,
  asset_description text,
  amount_range text,
  estimated_value numeric,
  filing_date date,
  source text,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_political_trades_symbol ON political_trades (symbol);
CREATE INDEX IF NOT EXISTS idx_political_trades_politician_name ON political_trades (politician_name);
CREATE INDEX IF NOT EXISTS idx_political_trades_transaction_date ON political_trades (transaction_date);
CREATE INDEX IF NOT EXISTS idx_political_trades_party ON political_trades (party);

-- Enable Row Level Security
ALTER TABLE political_trades ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY political_trades_select_policy ON political_trades
    FOR SELECT USING (true);

CREATE POLICY political_trades_insert_policy ON political_trades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY political_trades_update_policy ON political_trades
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

CREATE TRIGGER update_political_trades_updated_at
BEFORE UPDATE ON political_trades
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 