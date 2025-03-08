-- Drop existing tables if they exist
DROP TABLE IF EXISTS economic_reports;
DROP TABLE IF EXISTS economic_events;

-- Create the economic_reports table
CREATE TABLE economic_reports (
  id text PRIMARY KEY,
  source text NOT NULL,
  title text NOT NULL,
  report_date date,
  published_date date,
  url text,
  summary text,
  insights text,
  category text,
  file_url text,
  timestamp timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create the economic_events table
CREATE TABLE economic_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id text UNIQUE,
  event_name text NOT NULL,
  event_date date,
  country text,
  impact text,
  forecast text,
  previous text,
  actual text,
  event_time time,
  source text,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_economic_reports_source ON economic_reports (source);
CREATE INDEX IF NOT EXISTS idx_economic_reports_date ON economic_reports (report_date);
CREATE INDEX IF NOT EXISTS idx_economic_reports_category ON economic_reports (category);

CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events (event_date);
CREATE INDEX IF NOT EXISTS idx_economic_events_country ON economic_events (country);
CREATE INDEX IF NOT EXISTS idx_economic_events_impact ON economic_events (impact);
CREATE INDEX IF NOT EXISTS idx_economic_events_name ON economic_events (event_name);

-- Enable Row Level Security
ALTER TABLE economic_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE economic_events ENABLE ROW LEVEL SECURITY;

-- Create policies for economic_reports
CREATE POLICY economic_reports_select_policy ON economic_reports
    FOR SELECT USING (true);

CREATE POLICY economic_reports_insert_policy ON economic_reports
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY economic_reports_update_policy ON economic_reports
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Create policies for economic_events
CREATE POLICY economic_events_select_policy ON economic_events
    FOR SELECT USING (true);

CREATE POLICY economic_events_insert_policy ON economic_events
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY economic_events_update_policy ON economic_events
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

-- Create triggers for updated_at column
CREATE TRIGGER update_economic_reports_updated_at
BEFORE UPDATE ON economic_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_economic_events_updated_at
BEFORE UPDATE ON economic_events
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 