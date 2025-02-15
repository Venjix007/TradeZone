-- First, drop the existing check constraint
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;

-- Add new check constraint with our status values
ALTER TABLE orders 
ADD CONSTRAINT orders_status_check 
CHECK (status IN ('pending', 'completed', 'canceled'));
