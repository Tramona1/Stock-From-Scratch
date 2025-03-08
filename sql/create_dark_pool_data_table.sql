-- Drop the existing table if it exists
DROP TABLE IF EXISTS dark_pool_data;

-- Create the dark_pool_data table
CREATE TABLE dark_pool_data (
  id text PRIMARY KEY, -- Using ticker-date format as primary key
  symbol text NOT NULL,
  volume bigint,
  price numeric(15, 2),
  timestamp timestamp with time zone,
  blocks_count integer,
  total_premium numeric(15, 2),
  largest_block_size bigint,
  largest_block_price numeric(15, 2),
  largest_block_premium numeric(15, 2),
  most_recent_executed_at timestamp with time zone,
  data_date date,
  raw_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_dark_pool_data_symbol ON dark_pool_data (symbol);
CREATE INDEX IF NOT EXISTS idx_dark_pool_data_date ON dark_pool_data (data_date);
CREATE INDEX IF NOT EXISTS idx_dark_pool_data_volume ON dark_pool_data (volume);

-- Enable Row Level Security
ALTER TABLE dark_pool_data ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY dark_pool_data_select_policy ON dark_pool_data
    FOR SELECT USING (true);

CREATE POLICY dark_pool_data_insert_policy ON dark_pool_data
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY dark_pool_data_update_policy ON dark_pool_data
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
CREATE TRIGGER update_dark_pool_data_updated_at
BEFORE UPDATE ON dark_pool_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 