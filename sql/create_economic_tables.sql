-- Drop the existing economic_reports table if it exists
DROP TABLE IF EXISTS economic_reports;

-- Create the economic_reports table for major economic indicators and reports
CREATE TABLE economic_reports (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  report_name text NOT NULL,
  event_date timestamp with time zone,
  forecast text,
  previous text,
  actual text,
  importance text,
  category text,
  source text,
  report_period text,
  impact text,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  fetched_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_economic_reports_event_date ON economic_reports (event_date);
CREATE INDEX IF NOT EXISTS idx_economic_reports_report_name ON economic_reports (report_name);
CREATE INDEX IF NOT EXISTS idx_economic_reports_category ON economic_reports (category);

-- Enable Row Level Security
ALTER TABLE economic_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY economic_reports_select_policy ON economic_reports
    FOR SELECT USING (true);

CREATE POLICY economic_reports_insert_policy ON economic_reports
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY economic_reports_update_policy ON economic_reports
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Drop the existing economic_events table if it exists
DROP TABLE IF EXISTS economic_events;

-- Create the economic_events table for all economic calendar events
CREATE TABLE economic_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  event text NOT NULL,
  event_time timestamp with time zone,
  forecast text,
  previous text,
  reported_period text,
  type text,  -- fed-speaker, fomc, report
  importance text,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  fetched_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_economic_events_event_time ON economic_events (event_time);
CREATE INDEX IF NOT EXISTS idx_economic_events_type ON economic_events (type);

-- Enable Row Level Security
ALTER TABLE economic_events ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
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

-- Create trigger for updated_at column on economic_reports
CREATE TRIGGER update_economic_reports_updated_at
BEFORE UPDATE ON economic_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for updated_at column on economic_events
CREATE TRIGGER update_economic_events_updated_at
BEFORE UPDATE ON economic_events
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 