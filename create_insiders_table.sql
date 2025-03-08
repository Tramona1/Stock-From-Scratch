-- Drop the existing insiders table if it exists
DROP TABLE IF EXISTS insiders;

-- Create the insiders table
CREATE TABLE insiders (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  name text NOT NULL,
  title text,
  is_director boolean DEFAULT false,
  is_officer boolean DEFAULT false,
  is_ten_percent_owner boolean DEFAULT false,
  total_shares numeric,
  last_transaction_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_insiders_ticker ON insiders (ticker);
CREATE INDEX idx_insiders_name ON insiders (name);

-- Enable row level security
ALTER TABLE insiders ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read insiders
CREATE POLICY "Allow authenticated users to read insiders"
ON insiders
FOR SELECT 
TO authenticated
USING (true);

-- Allow service role to insert insiders
CREATE POLICY "Allow service role to insert insiders"
ON insiders
FOR INSERT 
TO service_role
WITH CHECK (true);

-- Allow service role to update insiders
CREATE POLICY "Allow service role to update insiders"
ON insiders 
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true); 