-- Drop the existing insider_flow table if it exists
DROP TABLE IF EXISTS insider_flow;

-- Create the insider_flow table
CREATE TABLE insider_flow (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  date date,
  transactions integer,
  volume numeric,
  avg_price numeric,
  premium numeric,
  buy_sell text,
  unique_insiders integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_insider_flow_ticker ON insider_flow (ticker);
CREATE INDEX idx_insider_flow_date ON insider_flow (date);
CREATE INDEX idx_insider_flow_buy_sell ON insider_flow (buy_sell);

-- Enable row level security
ALTER TABLE insider_flow ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read insider flow
CREATE POLICY "Allow authenticated users to read insider_flow"
ON insider_flow
FOR SELECT 
TO authenticated
USING (true);

-- Allow service role to insert insider flow
CREATE POLICY "Allow service role to insert insider_flow"
ON insider_flow
FOR INSERT 
TO service_role
WITH CHECK (true);

-- Allow service role to update insider flow
CREATE POLICY "Allow service role to update insider_flow"
ON insider_flow 
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true); 