-- Add admin policy for orders table
CREATE POLICY "Admins can manage all orders"
    ON orders FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );
