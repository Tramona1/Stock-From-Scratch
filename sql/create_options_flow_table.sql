-- Drop the existing options_flow table if it exists
DROP TABLE IF EXISTS options_flow;

-- Create the options_flow table
CREATE TABLE options_flow (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  date timestamp with time zone,
  contract_id text,
  strike_price numeric,
  expiration_date date,
  option_type text, -- 'call' or 'put'
  sentiment text,
  volume integer,
  open_interest integer,
  implied_volatility numeric,
  premium numeric,
  unusual_score numeric,
  trade_type text,
  raw_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_options_flow_ticker ON options_flow (ticker);
CREATE INDEX IF NOT EXISTS idx_options_flow_date ON options_flow (date);
CREATE INDEX IF NOT EXISTS idx_options_flow_option_type ON options_flow (option_type);
CREATE INDEX IF NOT EXISTS idx_options_flow_sentiment ON options_flow (sentiment);
CREATE INDEX IF NOT EXISTS idx_options_flow_expiration_date ON options_flow (expiration_date);

-- Enable Row Level Security
ALTER TABLE options_flow ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY options_flow_select_policy ON options_flow
    FOR SELECT USING (true);

CREATE POLICY options_flow_insert_policy ON options_flow
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY options_flow_update_policy ON options_flow
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

CREATE TRIGGER update_options_flow_updated_at
BEFORE UPDATE ON options_flow
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 