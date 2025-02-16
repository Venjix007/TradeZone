from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from datetime import datetime
from functools import wraps
import jwt
import random
from threading import Thread
import time

load_dotenv()

app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": ["https://benevolent-douhua-4258ca.netlify.app", "http://localhost:3000"]}}, supports_credentials=True)

# Configure CORS with more detailed settings
# CORS(app, resources={
#     r"/*": {
#         "origins": ["*"],
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
#         "supports_credentials": True,
#         "expose_headers": ["Content-Range", "X-Content-Range"]
#     }
# })

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://benevolent-douhua-4258ca.netlify.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Supabase Configuration
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            # Get user from database
            user = supabase.table('profiles').select('*').eq('user_id', data['user_id']).single().execute()
            
            if not user.data:
                return jsonify({'error': 'User not found'}), 401
                
            # Add is_admin flag to user data
            current_user = user.data
            current_user['user_id'] = data['user_id']
            current_user['is_admin'] = user.data.get('is_admin', False)
            
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated

# Admin verification decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            # Get user from database
            user = supabase.table('profiles').select('*').eq('user_id', data['user_id']).single().execute()
            
            if not user.data or not user.data.get('is_admin'):
                return jsonify({'error': 'Admin access required'}), 403
                
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated

# Global variable to control price update thread
price_update_running = True

# Order status constants
ORDER_STATUS_PENDING = 'pending'
ORDER_STATUS_COMPLETED = 'completed'
ORDER_STATUS_CANCELLED = 'cancelled'  # Using British spelling to match database constraint

def calculate_price_change(stock_id):
    """
    Calculate price change based on market demand and supply
    Returns the percentage change in price
    """
    try:
        # Get pending buy orders (demand)
        buy_orders = supabase.table('orders')\
            .select('quantity')\
            .eq('stock_id', stock_id)\
            .eq('type', 'buy')\
            .eq('status', 'pending')\
            .execute()
            
        total_demand = sum(float(order['quantity']) for order in buy_orders.data) if buy_orders.data else 0
        
        # Get pending sell orders (supply)
        sell_orders = supabase.table('orders')\
            .select('quantity')\
            .eq('stock_id', stock_id)\
            .eq('type', 'sell')\
            .eq('status', 'pending')\
            .execute()
            
        total_supply = sum(float(order['quantity']) for order in sell_orders.data) if sell_orders.data else 0
        
        if total_supply == 0:
            return 0  # No price change if there's no supply
            
        # Calculate demand/supply ratio
        ratio = total_demand / total_supply if total_supply > 0 else 1
        
        # Calculate price change percentage (max ±5%)
        if ratio > 1:  # More demand than supply
            change = min((ratio - 1) * 2, 0.05)  # Positive change
        else:  # More supply than demand
            change = max((ratio - 1) * 2, -0.05)  # Negative change
            
        return change
        
    except Exception as e:
        print(f"Error calculating price change: {str(e)}")
        return 0

def update_stock_prices():
    """
    Background thread function to update stock prices based on market demand and supply
    """
    while price_update_running:
        try:
            # Get all stocks
            stocks = supabase.table('stocks').select('*').execute()
            
            for stock in stocks.data:
                # Calculate price change based on market conditions
                change_percentage = calculate_price_change(stock['id'])
                
                if change_percentage != 0:  # Only update if there's a change
                    current_price = float(stock['current_price'])
                    new_price = round(current_price * (1 + change_percentage), 2)
                    
                    # Ensure price doesn't go below 1
                    new_price = max(1.0, new_price)
                    
                    # Update stock price in database
                    supabase.table('stocks').update({
                        'current_price': str(new_price),
                        'price_change': str(round(change_percentage * 100, 2))
                    }).eq('id', stock['id']).execute()
                
        except Exception as e:
            print(f"Error updating stock prices: {str(e)}")
            
        # Wait for 30 seconds before next update
        time.sleep(30)

def update_order_status(order_id, status, error=None, executed_price=None, executed_at=None):
    """
    Helper function to update order status and related fields
    """
    try:
        # Ensure status matches the database constraint
        valid_statuses = [ORDER_STATUS_PENDING, ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED]
        if status not in valid_statuses:
            print(f"Invalid status: {status}, valid statuses are: {valid_statuses}")
            status = ORDER_STATUS_CANCELLED
        
        # Start with basic update data
        update_data = {'status': status}
        
        # Add optional fields only if they are provided
        if executed_price is not None:
            update_data['price'] = str(executed_price)  # Use 'price' instead of 'executed_price'
        
        # Execute the update
        print(f"Updating order {order_id} with data: {update_data}")  # Debug log
        result = supabase.table('orders').update(update_data).eq('id', order_id).execute()
        
        if result.data:
            print(f"Successfully updated order {order_id} to status: {status}")
        else:
            print(f"Failed to update order {order_id}")
            
    except Exception as e:
        print(f"Error updating order status: {str(e)}")

def process_order(order_id, current_price):
    """
    Process a single order
    Returns True if order was processed successfully, False otherwise
    """
    try:
        # Get order details
        order = supabase.table('orders').select('*').eq('id', order_id).single().execute()
        if not order.data:
            return False
            
        order = order.data
        
        # Get user's profile
        user = supabase.table('profiles').select('*').eq('user_id', order['user_id']).single().execute()
        if not user.data:
            update_order_status(order_id, ORDER_STATUS_CANCELLED)
            return False
            
        user = user.data
        balance = float(user['balance'])
        
        if order['type'] == 'buy':
            total_cost = current_price * order['quantity']
            
            # Check if user has enough balance
            if balance < total_cost:
                update_order_status(order_id, ORDER_STATUS_CANCELLED)
                return False
                
            # Update user's balance
            new_balance = balance - total_cost
            supabase.table('profiles').update({'balance': str(new_balance)}).eq('user_id', order['user_id']).execute()
            
            # Update or create user's stock holding
            holdings = supabase.table('user_stocks').select('*').eq('user_id', order['user_id']).eq('stock_id', order['stock_id']).execute()
            
            if holdings.data:
                new_quantity = holdings.data[0]['quantity'] + order['quantity']
                supabase.table('user_stocks').update({'quantity': new_quantity}).eq('id', holdings.data[0]['id']).execute()
            else:
                supabase.table('user_stocks').insert({
                    'user_id': order['user_id'],
                    'stock_id': order['stock_id'],
                    'quantity': order['quantity']
                }).execute()
                
        else:  # sell order
            # Check if user has enough stocks
            holdings = supabase.table('user_stocks').select('*').eq('user_id', order['user_id']).eq('stock_id', order['stock_id']).execute()
            
            if not holdings.data or holdings.data[0]['quantity'] < order['quantity']:
                update_order_status(order_id, ORDER_STATUS_CANCELLED)
                return False
                
            total_value = current_price * order['quantity']
            
            # Update user's balance
            new_balance = balance + total_value
            supabase.table('profiles').update({'balance': str(new_balance)}).eq('user_id', order['user_id']).execute()
            
            # Update holdings
            new_quantity = holdings.data[0]['quantity'] - order['quantity']
            if new_quantity > 0:
                supabase.table('user_stocks').update({'quantity': new_quantity}).eq('id', holdings.data[0]['id']).execute()
            else:
                supabase.table('user_stocks').delete().eq('id', holdings.data[0]['id']).execute()
        
        # Mark order as completed with the current price
        update_order_status(order_id, ORDER_STATUS_COMPLETED, executed_price=current_price)
        
        # Record the transaction
        supabase.table('transactions').insert({
            'user_id': order['user_id'],
            'stock_id': order['stock_id'],
            'type': order['type'],
            'quantity': order['quantity'],
            'price': str(current_price),
            'total_amount': str(total_value if order['type'] == 'sell' else total_cost),
            'order_id': order_id,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return True
        
    except Exception as e:
        error_message = str(e)
        print(f"Error processing order: {error_message}")
        update_order_status(order_id, ORDER_STATUS_CANCELLED)
        return False

def process_pending_orders():
    """
    Background thread function to process pending orders
    """
    while True:
        try:
            if not check_market_state():
                # Cancel all pending orders if market is closed
                pending_orders = supabase.table('orders').select('*').eq('status', ORDER_STATUS_PENDING).execute()
                for order in pending_orders.data:
                    update_order_status(order['id'], ORDER_STATUS_CANCELLED)
                time.sleep(30)  # Wait longer when market is closed
                continue

            # Get all stocks to process orders stock by stock
            stocks = supabase.table('stocks').select('*').execute()
            
            for stock in stocks.data:
                stock_id = stock['id']
                current_price = float(stock['current_price'])
                
                # Get all pending orders for this stock
                # Use rpc call to bypass RLS
                pending_orders = supabase.rpc('get_pending_orders', {
                    'stock_id_param': stock_id
                }).execute()
                
                if not pending_orders.data:
                    continue
                
                print(f"Processing {len(pending_orders.data)} orders for stock {stock['symbol']}")
                
                # Wait for 2 minutes to collect orders
                time.sleep(120)
                
                # Get updated list of orders after waiting
                pending_orders = supabase.rpc('get_pending_orders', {
                    'stock_id_param': stock_id
                }).execute()
                
                if not pending_orders.data:
                    continue
                
                # Process all pending orders for this stock
                total_buy_quantity = 0
                total_sell_quantity = 0
                
                # First pass: calculate total buy and sell quantities
                for order in pending_orders.data:
                    if order['type'] == 'buy':
                        total_buy_quantity += order['quantity']
                    else:
                        total_sell_quantity += order['quantity']
                
                # Calculate new price based on supply and demand
                price_change = 0
                if total_buy_quantity > total_sell_quantity:
                    # More demand than supply, price goes up
                    price_change = 0.01 * (total_buy_quantity - total_sell_quantity) / 1000
                elif total_sell_quantity > total_buy_quantity:
                    # More supply than demand, price goes down
                    price_change = -0.01 * (total_sell_quantity - total_buy_quantity) / 1000
                
                new_price = round(current_price * (1 + price_change), 2)
                new_price = max(1.0, new_price)  # Ensure price doesn't go below 1
                
                # Update stock price using rpc call
                supabase.rpc('update_stock_price', {
                    'stock_id_param': stock_id,
                    'new_price_param': str(new_price),
                    'price_change_param': str(round(price_change * 100, 2))
                }).execute()
                
                # Second pass: process all orders with the new price
                for order in pending_orders.data:
                    success = process_order(order['id'], new_price)
                    if success:
                        print(f"Successfully processed order {order['id']}")
                    else:
                        print(f"Failed to process order {order['id']}")
                
        except Exception as e:
            print(f"Error in order processing thread: {str(e)}")
            
        time.sleep(5)  # Small delay before next iteration

# Start both price update and order processing threads
price_update_thread = Thread(target=update_stock_prices, daemon=True)
order_processing_thread = Thread(target=process_pending_orders, daemon=True)
price_update_thread.start()
order_processing_thread.start()

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        print("Received registration data:", data)
        
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
            
        password = data.get('password')
        if not password:
            return jsonify({'error': 'Password is required'}), 400
            
        role = data.get('role', 'user')
        
        # Validate role
        if role not in ['user', 'admin']:
            return jsonify({'error': 'Invalid role specified'}), 400
        
        # Register user in Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not response.user or not response.user.id:
            return jsonify({'error': 'Failed to create user in Supabase'}), 400
        
        # Create user profile with initial balance
        user_data = {
            'user_id': response.user.id,
            'email': email,
            'role': role,
            'balance': 10000.00 if role == 'user' else 1000000000.00,
            'created_at': datetime.utcnow().isoformat()
        }
        
        print("Creating user profile:", user_data)
        
        # Insert profile
        profile_response = supabase.table('profiles').insert(user_data).execute()
        
        # If user is admin, add initial stock holdings
        if role == 'admin':
            print("Adding initial stocks for admin user")
            success = add_initial_admin_stocks(response.user.id)
            if not success:
                print("Warning: Failed to add initial admin stocks")
        
        return jsonify({'message': 'Registration successful'}), 201
    except Exception as e:
        print("Registration error:", str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        # Sign in user
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Get user profile
        user_profile = supabase.table('profiles').select('*').eq('user_id', response.user.id).execute()
        
        # Create JWT token
        token = jwt.encode({
            'user_id': response.user.id,
            'email': email,
            'role': user_profile.data[0]['role']
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': response.user.id,
                'email': email,
                'role': user_profile.data[0]['role']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 401

# Market Control Routes (Admin Only)
def check_market_state():
    """
    Check if the market is currently active
    Returns True if market is active, False otherwise
    """
    try:
        market_state = supabase.table('market_state').select('*').single().execute()
        return market_state.data['is_active'] if market_state.data else False
    except Exception as e:
        print(f"Error checking market state: {str(e)}")
        return False

@app.route('/api/market/state', methods=['GET'])
@admin_required
def get_market_state():
    """Get current market state"""
    try:
        market_state = supabase.table('market_state').select('*').single().execute()
        return jsonify({
            'is_active': market_state.data['is_active'] if market_state.data else False,
            'message': 'Market is currently ' + ('active' if market_state.data and market_state.data['is_active'] else 'inactive')
        })
    except Exception as e:
        print(f"Error getting market state: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/control', methods=['POST'])
@admin_required
def control_market():
    """Control market state - only accessible by admin users"""
    try:
        data = request.get_json()
        if not data or 'is_active' not in data:
            return jsonify({'error': 'Missing is_active field'}), 400

        # Update market state
        new_state = bool(data['is_active'])
        result = supabase.table('market_state').update({'is_active': new_state}).eq('id', 1).execute()
        
        if not result.data:
            return jsonify({'error': 'Failed to update market state'}), 500
            
        return jsonify({
            'message': f'Market {"started" if new_state else "stopped"} successfully',
            'is_active': new_state
        })
    except Exception as e:
        print(f"Error controlling market: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Stock Routes
@app.route('/api/stocks', methods=['GET'])
@token_required
def get_stocks(current_user):
    try:
        stocks = supabase.table('stocks').select('*').execute()
        return jsonify(stocks.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks/buy', methods=['POST'])
@token_required
def buy_stock(current_user):
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        quantity = int(data.get('quantity', 0))
        
        if not stock_id or quantity <= 0:
            return jsonify({
                'error': 'Invalid stock_id or quantity',
                'showAlert': True,
                'alertMessage': 'Please provide valid stock and quantity values.'
            }), 400
            
        # Get stock details
        stock = supabase.table('stocks').select('*').eq('id', stock_id).execute()
        if not stock.data:
            return jsonify({
                'error': 'Stock not found',
                'showAlert': True,
                'alertMessage': 'The requested stock was not found.'
            }), 404
            
        stock = stock.data[0]
        # Convert price from USD to INR (using a fixed rate of 1 USD = 83 INR)
        inr_price = float(stock['current_price']) * 83
        total_cost = inr_price * quantity
        
        # Get user's balance
        user = supabase.table('profiles').select('balance').eq('user_id', current_user['user_id']).execute()
        if not user.data:
            return jsonify({
                'error': 'User not found',
                'showAlert': True,
                'alertMessage': 'User profile not found. Please try again.'
            }), 404
            
        balance = float(user.data[0]['balance'])
        
        if balance < total_cost:
            return jsonify({
                'error': 'Insufficient balance',
                'showAlert': True,
                'alertMessage': f'Insufficient funds. Required: ₹{total_cost:.2f}, Available: ₹{balance:.2f}'
            }), 400
            
        # Create buy order
        order = {
            'user_id': current_user['user_id'],
            'stock_id': stock_id,
            'type': 'buy',
            'quantity': quantity,
            'price': str(inr_price),  # Store price in INR
            'status': ORDER_STATUS_PENDING,
            'created_at': datetime.now().isoformat()
        }
        
        # Update user's balance and stock holdings
        new_balance = balance - total_cost
        supabase.table('profiles').update({'balance': str(new_balance)}).eq('user_id', current_user['user_id']).execute()
        
        # Update or create user's stock holding
        holdings = supabase.table('user_stocks').select('*').eq('user_id', current_user['user_id']).eq('stock_id', stock_id).execute()
        
        if holdings.data:
            new_quantity = holdings.data[0]['quantity'] + quantity
            supabase.table('user_stocks').update({'quantity': new_quantity}).eq('id', holdings.data[0]['id']).execute()
        else:
            supabase.table('user_stocks').insert({
                'user_id': current_user['user_id'],
                'stock_id': stock_id,
                'quantity': quantity
            }).execute()
            
        # Record the transaction
        supabase.table('transactions').insert(order).execute()
        
        return jsonify({
            'message': 'Stock purchased successfully',
            'new_balance': new_balance,
            'showAlert': True,
            'alertMessage': f'Successfully purchased {quantity} shares for ₹{total_cost:.2f}'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'showAlert': True,
            'alertMessage': f'Error occurred: {str(e)}'
        }), 500

@app.route('/api/stocks/sell', methods=['POST'])
@token_required
def sell_stock(current_user):
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        quantity = int(data.get('quantity', 0))
        
        if not stock_id or quantity <= 0:
            return jsonify({
                'error': 'Invalid stock_id or quantity',
                'showAlert': True,
                'alertMessage': 'Please provide valid stock and quantity values.'
            }), 400
            
        # Get stock details
        stock = supabase.table('stocks').select('*').eq('id', stock_id).execute()
        if not stock.data:
            return jsonify({
                'error': 'Stock not found',
                'showAlert': True,
                'alertMessage': 'The requested stock was not found.'
            }), 404
            
        stock = stock.data[0]
        # Convert price from USD to INR (using a fixed rate of 1 USD = 83 INR)
        inr_price = float(stock['current_price']) * 83
        total_value = inr_price * quantity
        
        # Check if user has enough stocks
        holdings = supabase.table('user_stocks').select('*').eq('user_id', current_user['user_id']).eq('stock_id', stock_id).execute()
        
        if not holdings.data or holdings.data[0]['quantity'] < quantity:
            available_quantity = holdings.data[0]['quantity'] if holdings.data else 0
            return jsonify({
                'error': 'Insufficient stocks',
                'showAlert': True,
                'alertMessage': f'Not enough stocks available. Requested: {quantity}, Available: {available_quantity}'
            }), 400
            
        # Get user's current balance
        user = supabase.table('profiles').select('balance').eq('user_id', current_user['user_id']).execute()
        current_balance = float(user.data[0]['balance'])
        
        # Create sell order
        order = {
            'user_id': current_user['user_id'],
            'stock_id': stock_id,
            'type': 'sell',
            'quantity': quantity,
            'price': str(inr_price),  # Store price in INR
            'status': ORDER_STATUS_PENDING,
            'created_at': datetime.now().isoformat()
        }
        
        # Update user's balance and stock holdings
        new_balance = current_balance + total_value
        supabase.table('profiles').update({'balance': str(new_balance)}).eq('user_id', current_user['user_id']).execute()
        
        # Update holdings
        new_quantity = holdings.data[0]['quantity'] - quantity
        if new_quantity > 0:
            supabase.table('user_stocks').update({'quantity': new_quantity}).eq('id', holdings.data[0]['id']).execute()
        else:
            supabase.table('user_stocks').delete().eq('id', holdings.data[0]['id']).execute()
            
        # Record the transaction
        supabase.table('transactions').insert(order).execute()
        
        return jsonify({
            'message': 'Stock sold successfully',
            'new_balance': new_balance,
            'showAlert': True,
            'alertMessage': f'Successfully sold {quantity} shares for ₹{total_value:.2f}'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'showAlert': True,
            'alertMessage': f'Error occurred: {str(e)}'
        }), 500

# Orders Routes
@app.route('/api/orders', methods=['POST'])
@token_required
def place_order(current_user):
    try:
        # Check if market is active
        if not check_market_state():
            return jsonify({'error': 'Market is currently closed. Orders cannot be placed.'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['stock_id', 'type', 'quantity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate order type
        if data['type'] not in ['buy', 'sell']:
            return jsonify({'error': 'Invalid order type'}), 400
            
        # Get current stock price
        stock = supabase.table('stocks').select('current_price').eq('id', data['stock_id']).single().execute()
        if not stock.data:
            return jsonify({'error': 'Stock not found'}), 404
            
        current_price = stock.data['current_price']
            
        # Create order
        order = {
            'user_id': current_user['user_id'],
            'stock_id': data['stock_id'],
            'type': data['type'],
            'quantity': data['quantity'],
            'price': current_price,  # Add current price
            'status': ORDER_STATUS_PENDING,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('orders').insert(order).execute()
        
        return jsonify({
            'message': 'Order placed successfully',
            'order_id': result.data[0]['id']
        })
        
    except Exception as e:
        print(f"Error placing order: {str(e)}")  # Add error logging
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@token_required
def get_user_orders(current_user):
    try:
        # Get user's orders with stock information
        response = supabase.from_('orders') \
            .select('*, stocks(symbol)') \
            .eq('user_id', current_user['user_id']) \
            .execute()
        
        # Format the response
        orders = []
        for order in response.data:
            orders.append({
                'id': order['id'],
                'stock_symbol': order['stocks']['symbol'],
                'type': order['type'],
                'quantity': order['quantity'],
                'price': float(order['price']),
                'status': order['status'],
                'created_at': order['created_at']
            })
        
        return jsonify(orders), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Portfolio Routes
@app.route('/api/portfolio/profile', methods=['GET'])
@token_required
def get_user_profile(current_user):
    try:
        # Get user profile with balance
        profile = supabase.table('profiles') \
            .select('*') \
            .eq('user_id', current_user['user_id']) \
            .single() \
            .execute()

        # Get user's stock holdings with current prices
        holdings = supabase.table('user_stocks') \
            .select('*, stocks(*)') \
            .eq('user_id', current_user['user_id']) \
            .execute()

        # Calculate total portfolio value
        total_portfolio_value = float(profile.data['balance'])  # Start with cash balance
        
        for holding in holdings.data:
            stock_value = holding['quantity'] * float(holding['stocks']['current_price'])
            total_portfolio_value += stock_value

        response_data = {
            'balance': float(profile.data['balance']),
            'total_portfolio_value': total_portfolio_value
        }

        return jsonify(response_data), 200
    except Exception as e:
        print("Error fetching portfolio:", str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/portfolio/holdings', methods=['GET'])
@token_required
def get_user_holdings(current_user):
    try:
        # Get user's stock holdings with stock information
        holdings = supabase.table('user_stocks') \
            .select('*, stocks(*)') \
            .eq('user_id', current_user['user_id']) \
            .execute()

        # Format the response
        formatted_holdings = []
        for holding in holdings.data:
            stock = holding['stocks']
            formatted_holdings.append({
                'stock_id': stock['id'],
                'stock_name': stock['name'],
                'stock_symbol': stock['symbol'],
                'quantity': holding['quantity'],
                'current_price': float(stock['current_price']),
                'total_value': holding['quantity'] * float(stock['current_price'])
            })

        return jsonify(formatted_holdings), 200
    except Exception as e:
        print("Error fetching holdings:", str(e))
        return jsonify({'error': str(e)}), 400

# News Routes
@app.route('/api/news', methods=['GET'])
@token_required
def get_news(current_user):
    try:
        news = supabase.table('news').select('*').order('created_at', desc=True).execute()
        return jsonify(news.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['POST'])
@admin_required
def create_news():
    data = request.json
    try:
        news_data = {
            'title': data.get('title'),
            'content': data.get('content'),
            'created_at': datetime.utcnow().isoformat()
        }
        supabase.table('news').insert(news_data).execute()
        return jsonify({'message': 'News created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Leaderboard Route (Admin Only)
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get user leaderboard based on portfolio value"""
    try:
        # Get all users with their stock holdings
        users = supabase.table('profiles').select('*').execute()
        leaderboard = []
        
        for user in users.data:
            # Get user's stock holdings
            holdings = supabase.table('user_stocks').select('*').eq('user_id', user['user_id']).execute()
            
            # Get current stock prices
            total_value = float(user['balance'])  # Start with cash balance
            
            for holding in holdings.data:
                stock = supabase.table('stocks').select('current_price').eq('id', holding['stock_id']).single().execute()
                if stock.data:
                    stock_value = float(stock.data['current_price']) * holding['quantity']
                    total_value += stock_value
            
            leaderboard.append({
                'user_id': user['user_id'],
                'email': user['email'],
                'total_value': total_value
            })
        
        # Sort by total value descending
        leaderboard.sort(key=lambda x: x['total_value'], reverse=True)
        
        return jsonify(leaderboard)
    except Exception as e:
        print(f"Error fetching leaderboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

def add_initial_admin_stocks(user_id):
    try:
        # Get all stocks
        stocks_response = supabase.table('stocks').select('id').execute()
        
        if not stocks_response.data:
            print("No stocks found in database")
            return False
            
        print(f"Adding {len(stocks_response.data)} stocks to admin portfolio")
        
        # Add 1000 shares of each stock to admin's portfolio
        for stock in stocks_response.data:
            stock_data = {
                'user_id': user_id,
                'stock_id': stock['id'],
                'quantity': 1000
            }
            try:
                insert_response = supabase.table('user_stocks').insert(stock_data).execute()
                print(f"Added stock {stock['id']} to admin portfolio")
            except Exception as e:
                print(f"Error adding stock {stock['id']}: {str(e)}")
                # If insert fails, try to update existing holding
                try:
                    update_response = supabase.table('user_stocks') \
                    .update({'quantity': 1000}) \
                    .eq('user_id', user_id) \
                    .eq('stock_id', stock['id']) \
                    .execute()
                    print(f"Updated existing stock {stock['id']} in admin portfolio")
                except Exception as update_error:
                    print(f"Error updating stock {stock['id']}: {str(update_error)}")
                    continue
        
        return True
    except Exception as e:
        print("Error adding initial admin stocks:", str(e))
        return False

# Admin stock management
@app.route('/api/admin/ensure-stocks', methods=['POST'])
@token_required
def ensure_admin_stocks(current_user):
    try:
        # Check if user is admin
        profile = supabase.table('profiles') \
            .select('role') \
            .eq('user_id', current_user['user_id']) \
            .single() \
            .execute()
            
        if not profile.data or profile.data['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        # Add initial stocks
        success = add_initial_admin_stocks(current_user['user_id'])
        
        if success:
            return jsonify({'message': 'Admin stocks verified and updated'}), 200
        else:
            return jsonify({'error': 'Failed to update admin stocks'}), 500
            
    except Exception as e:
        print("Error ensuring admin stocks:", str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/stocks/add', methods=['POST'])
@token_required
@admin_required
def add_new_stock(current_user):
    try:
        data = request.get_json()
        
        # Required fields for a new stock
        required_fields = ['symbol', 'name', 'current_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new stock in stocks table
        new_stock = supabase.table('stocks').insert({
            'symbol': data['symbol'].upper(),
            'name': data['name'],
            'current_price': float(data['current_price']),
            # 'description': data['description']
        }).execute()
        
        if not new_stock.data:
            return jsonify({'error': 'Failed to create stock'}), 500
            
        stock_id = new_stock.data[0]['id']
        
        # Add initial stock quantity to admin's portfolio
        initial_quantity = 1000
        user_stock = supabase.table('user_stocks').insert({
            'user_id': current_user['user_id'],
            'stock_id': stock_id,
            'quantity': initial_quantity
        }).execute()
        
        if not user_stock.data:
            # Rollback stock creation if portfolio update fails
            supabase.table('stocks').delete().eq('id', stock_id).execute()
            return jsonify({'error': 'Failed to add stock to admin portfolio'}), 500
            
        return jsonify({
            'message': 'Stock added successfully',
            'stock': new_stock.data[0],
            'initial_quantity': initial_quantity
        }), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000,debug=True)
