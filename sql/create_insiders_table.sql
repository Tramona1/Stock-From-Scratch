-- Drop the existing insiders table if it exists
DROP TABLE IF EXISTS insiders;

-- Create the insiders table
CREATE TABLE insiders (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  name text NOT NULL,
  display_name text,
  insider_id text,
  title text,
  is_person boolean DEFAULT true,
  is_director boolean DEFAULT false,
  is_officer boolean DEFAULT false,
  is_ten_percent_owner boolean DEFAULT false,
  logo_url text,
  name_slug text,
  social_links jsonb,
  total_shares numeric,
  last_transaction_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_insiders_ticker ON insiders (ticker);
CREATE INDEX IF NOT EXISTS idx_insiders_name ON insiders (name);
CREATE INDEX IF NOT EXISTS idx_insiders_insider_id ON insiders (insider_id);

-- Enable Row Level Security
ALTER TABLE insiders ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY insiders_select_policy ON insiders
    FOR SELECT USING (true);

CREATE POLICY insiders_insert_policy ON insiders
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY insiders_update_policy ON insiders
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

CREATE TRIGGER update_insiders_updated_at
BEFORE UPDATE ON insiders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 