
-- Create profiles table
CREATE TABLE profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    balance DECIMAL(20, 2) NOT NULL DEFAULT 10000.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for profiles table
CREATE POLICY "Enable insert for registration" ON profiles
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Admins can do all" ON profiles
    FOR ALL
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE role = 'admin'
        )
    );

-- Create stocks table
CREATE TABLE stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    symbol TEXT NOT NULL UNIQUE,
    current_price DECIMAL(15, 2) NOT NULL,
    price_change DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(user_id),
    stock_id UUID REFERENCES stocks(id),
    type TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(15, 2) NOT NULL CHECK (price > 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_stocks table
CREATE TABLE user_stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(user_id),
    stock_id UUID REFERENCES stocks(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stock_id)
);

-- Create news table
CREATE TABLE news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create market_state table
CREATE TABLE market_state (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    is_active BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial market state
INSERT INTO market_state (is_active) VALUES (true);

-- Create sample stocks
INSERT INTO stocks (name, symbol, current_price) VALUES
    ('Apple Inc.', 'AAPL', 150.00),
    ('Microsoft Corporation', 'MSFT', 280.00),
    ('Amazon.com Inc.', 'AMZN', 3300.00),
    ('Alphabet Inc.', 'GOOGL', 2800.00),
    ('Tesla Inc.', 'TSLA', 750.00);

-- Add initial stocks to admin portfolios
DO $$
DECLARE
    admin_id UUID;
    stock_id UUID;
BEGIN
    -- For each admin
    FOR admin_id IN SELECT user_id FROM profiles WHERE role = 'admin' LOOP
        -- For each stock
        FOR stock_id IN SELECT id FROM stocks LOOP
            -- Add 1000 shares if they don't already have it
            INSERT INTO user_stocks (user_id, stock_id, quantity)
            VALUES (admin_id, stock_id, 1000)
            ON CONFLICT (user_id, stock_id) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;

-- Enable Row Level Security (RLS)
ALTER TABLE stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE news ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_state ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Stocks policies
CREATE POLICY "Stocks are viewable by everyone"
    ON stocks FOR SELECT
    USING (true);

CREATE POLICY "Only admins can insert stocks"
    ON stocks FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM profiles
        WHERE user_id = auth.uid()
        AND role = 'admin'
    ));

CREATE POLICY "Only admins can update stocks"
    ON stocks FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM profiles
        WHERE user_id = auth.uid()
        AND role = 'admin'
    ));

-- Orders policies
CREATE POLICY "Users can view own orders"
    ON orders FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own orders"
    ON orders FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own orders"
    ON orders FOR UPDATE
    USING (auth.uid() = user_id);

-- User stocks policies
CREATE POLICY "Users can view own stocks"
    ON user_stocks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own stocks"
    ON user_stocks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own stocks"
    ON user_stocks FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own stocks"
    ON user_stocks FOR DELETE
    USING (auth.uid() = user_id);

CREATE POLICY "Admins can manage all stocks"
    ON user_stocks FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );

-- News policies
CREATE POLICY "News is viewable by everyone"
    ON news FOR SELECT
    USING (true);

CREATE POLICY "Only admins can insert news"
    ON news FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM profiles
        WHERE user_id = auth.uid()
        AND role = 'admin'
    ));

-- Market state policies
CREATE POLICY "Market state is viewable by everyone"
    ON market_state FOR SELECT
    USING (true);

CREATE POLICY "Only admins can update market state"
    ON market_state FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM profiles
        WHERE user_id = auth.uid()
        AND role = 'admin'
    ));
