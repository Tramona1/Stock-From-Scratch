-- Function to update subscription with string ID instead of UUID
CREATE OR REPLACE FUNCTION update_subscription_with_string_id(
  p_user_id TEXT,
  p_subscription_id TEXT,
  p_subscription_status TEXT,
  p_plan_type TEXT,
  p_is_annual BOOLEAN,
  p_current_period_end TIMESTAMPTZ,
  p_cancel_at_period_end BOOLEAN
) RETURNS VOID AS $$
BEGIN
  -- Update the subscription data directly with text ID
  UPDATE public.users
  SET 
    subscription_id = p_subscription_id,
    subscription_status = p_subscription_status,
    plan_type = p_plan_type,
    is_annual = p_is_annual,
    current_period_end = p_current_period_end,
    cancel_at_period_end = p_cancel_at_period_end,
    updated_at = NOW()
  WHERE id::TEXT = p_user_id;
END;
$$ LANGUAGE plpgsql; 