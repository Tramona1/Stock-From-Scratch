-- Drop the existing insider_trades table if it exists
DROP TABLE IF EXISTS insider_trades;

-- Create the insider_trades table with the correct schema
CREATE TABLE insider_trades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  filing_id uuid NOT NULL,
  symbol text NOT NULL,
  company_name text,
  insider_name text,
  insider_title text,
  transaction_type text,
  transaction_date date,
  shares numeric,
  price numeric,
  total_value numeric,
  shares_owned_after numeric,
  filing_date date,
  source text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_insider_trades_symbol ON insider_trades (symbol);
CREATE INDEX idx_insider_trades_transaction_date ON insider_trades (transaction_date);
CREATE INDEX idx_insider_trades_filing_id ON insider_trades (filing_id);

-- Enable row level security
ALTER TABLE insider_trades ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read insider trades
CREATE POLICY "Allow authenticated users to read insider_trades"
ON insider_trades
FOR SELECT 
TO authenticated
USING (true);

-- Allow service role to insert insider trades
CREATE POLICY "Allow service role to insert insider_trades"
ON insider_trades
FOR INSERT 
TO service_role
WITH CHECK (true);

-- Allow service role to update insider trades
CREATE POLICY "Allow service role to update insider_trades"
ON insider_trades 
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true); 