-- Function to get pending orders for a stock
CREATE OR REPLACE FUNCTION get_pending_orders(stock_id_param UUID)
RETURNS SETOF orders
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM orders
    WHERE status = 'pending'
    AND stock_id = stock_id_param
    ORDER BY created_at;
END;
$$;

-- Function to update stock price
CREATE OR REPLACE FUNCTION update_stock_price(
    stock_id_param UUID,
    new_price_param TEXT,
    price_change_param TEXT
)
RETURNS void
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE stocks
    SET current_price = new_price_param::DECIMAL,
        price_change = price_change_param::DECIMAL
    WHERE id = stock_id_param;
END;
$$;
