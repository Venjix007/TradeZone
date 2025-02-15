-- Add execution details columns to orders table
ALTER TABLE orders
ADD COLUMN executed_price DECIMAL(15, 2),
ADD COLUMN executed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN error TEXT;
