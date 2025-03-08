-- Function to get subscription with string ID instead of UUID
CREATE OR REPLACE FUNCTION get_subscription_by_string_id(
  p_user_id TEXT
) RETURNS TABLE (
  subscription_status TEXT,
  subscription_id TEXT,
  plan_type TEXT,
  is_annual BOOLEAN,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.subscription_status,
    u.subscription_id,
    u.plan_type,
    u.is_annual,
    u.current_period_end,
    u.cancel_at_period_end
  FROM 
    public.users u
  WHERE 
    u.id::TEXT = p_user_id;
END;
$$ LANGUAGE plpgsql; 