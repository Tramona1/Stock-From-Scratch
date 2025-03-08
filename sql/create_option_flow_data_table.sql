-- Drop the existing table if it exists
DROP TABLE IF EXISTS option_flow_data;

-- Create the option_flow_data table
CREATE TABLE option_flow_data (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  analysis_date date NOT NULL,
  flow_count integer,
  bullish_count integer,
  bearish_count integer,
  high_premium_count integer,
  pre_earnings_count integer,
  total_premium numeric,
  bullish_premium numeric,
  bearish_premium numeric,
  sentiment text,
  raw_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  
  -- Composite unique constraint 
  UNIQUE(ticker, analysis_date)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_option_flow_ticker ON option_flow_data (ticker);
CREATE INDEX IF NOT EXISTS idx_option_flow_date ON option_flow_data (analysis_date);
CREATE INDEX IF NOT EXISTS idx_option_flow_sentiment ON option_flow_data (sentiment);

-- Enable Row Level Security
ALTER TABLE option_flow_data ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY option_flow_select_policy ON option_flow_data
    FOR SELECT USING (true);

CREATE POLICY option_flow_insert_policy ON option_flow_data
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY option_flow_update_policy ON option_flow_data
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
CREATE TRIGGER update_option_flow_updated_at
BEFORE UPDATE ON option_flow_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 