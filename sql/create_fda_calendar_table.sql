-- Drop the existing fda_calendar table if it exists
DROP TABLE IF EXISTS fda_calendar;

-- Create the fda_calendar table with proper columns
CREATE TABLE fda_calendar (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ticker text NOT NULL,
  drug text,
  description text,
  catalyst text,
  indication text,
  start_date date,
  end_date date,
  outcome text,
  outcome_brief text,
  status text,
  notes text,
  source_link text,
  marketcap numeric,
  has_options boolean,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  fetched_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_fda_calendar_ticker ON fda_calendar (ticker);
CREATE INDEX IF NOT EXISTS idx_fda_calendar_start_date ON fda_calendar (start_date);
CREATE INDEX IF NOT EXISTS idx_fda_calendar_catalyst ON fda_calendar (catalyst);
CREATE INDEX IF NOT EXISTS idx_fda_calendar_drug ON fda_calendar (drug);

-- Enable Row Level Security
ALTER TABLE fda_calendar ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY fda_calendar_select_policy ON fda_calendar
    FOR SELECT USING (true);

CREATE POLICY fda_calendar_insert_policy ON fda_calendar
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY fda_calendar_update_policy ON fda_calendar
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
CREATE TRIGGER update_fda_calendar_updated_at
BEFORE UPDATE ON fda_calendar
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 