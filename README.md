# Chesa Stock Exchange

A full-stack virtual stock market platform with role-based authentication, real-time trading, and market control features.

## Features

- Role-based authentication (Admin and Regular Users)
- Real-time stock trading
- Market news system
- Portfolio management
- Admin dashboard with market control
- Leaderboard system

## Tech Stack

- Frontend: React with TypeScript, Material-UI
- Backend: Flask
- Database: Supabase
- Authentication: JWT

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- Supabase account

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example` and add your Supabase credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret
```

5. Run the backend server:
```bash
python app.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## Database Schema

### Tables

1. profiles
   - user_id (primary key)
   - email
   - role (admin/user)
   - balance
   - created_at

2. stocks
   - id (primary key)
   - name
   - symbol
   - current_price
   - price_change
   - created_at

3. orders
   - id (primary key)
   - user_id (foreign key)
   - stock_id (foreign key)
   - type (buy/sell)
   - quantity
   - price
   - status (pending/completed)
   - created_at

4. user_stocks
   - id (primary key)
   - user_id (foreign key)
   - stock_id (foreign key)
   - quantity
   - created_at

5. news
   - id (primary key)
   - title
   - content
   - created_at

6. market_state
   - id (primary key)
   - is_active
   - updated_at

## API Endpoints

### Authentication
- POST /api/auth/register
- POST /api/auth/login

### Market
- GET /api/stocks
- POST /api/orders
- GET /api/orders

### Portfolio
- GET /api/portfolio/holdings
- GET /api/portfolio/profile

### News
- GET /api/news
- POST /api/news (Admin only)

### Admin
- POST /api/market/control (Admin only)
- GET /api/leaderboard (Admin only)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License.
