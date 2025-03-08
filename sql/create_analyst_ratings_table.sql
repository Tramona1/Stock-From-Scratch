-- Drop the existing analyst_ratings table if it exists
DROP TABLE IF EXISTS analyst_ratings;

-- Create the analyst_ratings table with the correct schema
CREATE TABLE analyst_ratings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol text NOT NULL,
  company_name text,
  firm text NOT NULL,
  analyst text,
  new_rating text,
  old_rating text,
  rating_change text,
  new_price_target numeric,
  old_price_target numeric,
  price_target_change_percent numeric,
  current_price numeric,
  sector text,
  rating_date date,
  action text,
  source text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_analyst_ratings_symbol ON analyst_ratings (symbol);
CREATE INDEX idx_analyst_ratings_rating_date ON analyst_ratings (rating_date);
CREATE INDEX idx_analyst_ratings_firm ON analyst_ratings (firm);

-- Enable row level security
ALTER TABLE analyst_ratings ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read analyst ratings
CREATE POLICY "Allow authenticated users to read analyst_ratings"
ON analyst_ratings
FOR SELECT 
TO authenticated
USING (true);

-- Allow service role to insert analyst ratings
CREATE POLICY "Allow service role to insert analyst_ratings"
ON analyst_ratings
FOR INSERT 
TO service_role
WITH CHECK (true);

-- Allow service role to update analyst ratings
CREATE POLICY "Allow service role to update analyst_ratings"
ON analyst_ratings 
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true); 