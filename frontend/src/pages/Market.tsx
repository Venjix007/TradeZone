import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import axios from 'axios';

interface Stock {
  id: string;
  name: string;
  symbol: string;
  current_price: number;
  price_change: number;
}

interface Order {
  id: string;
  stock_id: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
}

const Market = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    fetchStocks();
  }, []);

  const fetchStocks = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/stocks');
      setStocks(response.data);
    } catch (error) {
      console.error('Error fetching stocks:', error);
    }
  };

  const handleOrderClick = (stock: Stock, type: 'buy' | 'sell') => {
    setSelectedStock(stock);
    setOrderType(type);
    setQuantity('');
    setPrice(type === 'buy' ? stock.current_price.toString() : '');
    fetchOrders(stock.id, type === 'buy' ? 'sell' : 'buy');
    setOpenDialog(true);
  };

  const fetchOrders = async (stockId: string, type: 'buy' | 'sell') => {
    try {
      const response = await axios.get(`http://localhost:5000/api/orders?stock_id=${stockId}&type=${type}`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const handlePlaceOrder = async () => {
    if (!selectedStock) return;

    try {
      await axios.post('http://localhost:5000/api/orders', {
        stock_id: selectedStock.id,
        type: orderType,
        quantity: parseInt(quantity),
        price: parseFloat(price),
      });
      setOpenDialog(false);
      fetchStocks(); // Refresh stocks after order
    } catch (error) {
      console.error('Error placing order:', error);
    }
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Market
      </Typography>
      <Grid container spacing={3}>
        {stocks.map((stock) => (
          <Grid item xs={12} sm={6} md={4} key={stock.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{stock.name}</Typography>
                <Typography color="textSecondary">{stock.symbol}</Typography>
                <Typography variant="h5" sx={{ my: 2 }}>
                  ${stock.current_price.toFixed(2)}
                </Typography>
                <Typography
                  color={stock.price_change >= 0 ? 'success.main' : 'error.main'}
                >
                  {stock.price_change >= 0 ? '+' : ''}
                  {stock.price_change.toFixed(2)}%
                </Typography>
                <Grid container spacing={1} sx={{ mt: 2 }}>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      onClick={() => handleOrderClick(stock, 'buy')}
                    >
                      Buy
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="secondary"
                      onClick={() => handleOrderClick(stock, 'sell')}
                    >
                      Sell
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {orderType === 'buy' ? 'Buy' : 'Sell'} {selectedStock?.name}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Quantity"
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Price"
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            margin="normal"
          />
          <Typography variant="h6" sx={{ mt: 2 }}>
            {orderType === 'buy' ? 'Sell' : 'Buy'} Orders
          </Typography>
          <List>
            {orders.map((order) => (
              <ListItem key={order.id}>
                <ListItemText
                  primary={`${order.quantity} shares at $${order.price}`}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handlePlaceOrder} variant="contained" color="primary">
            Place Order
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Market;
