import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Container,
  Typography,
  Box,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Grid,
} from '@mui/material';

interface LeaderboardEntry {
  user_id: string;
  email: string;
  total_value: number;
}

interface NewStock {
  symbol: string;
  name: string;
  current_price: string;
}

const AdminDashboard: React.FC = () => {
  const [marketActive, setMarketActive] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [newStock, setNewStock] = useState<NewStock>({
    symbol: '',
    name: '',
    current_price: ''
  });
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is admin
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchMarketState();
    fetchLeaderboard();
  }, [navigate]);

  const fetchMarketState = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/market/state', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMarketActive(response.data.is_active);
      setError('');
    } catch (error: any) {
      console.error('Error fetching market state:', error);
      setError(error.response?.data?.error || 'Failed to fetch market state');
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/leaderboard', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeaderboard(response.data);
      setError('');
    } catch (error: any) {
      console.error('Error fetching leaderboard:', error);
      setError(error.response?.data?.error || 'Failed to fetch leaderboard');
    }
  };

  const handleMarketControl = async () => {
    try {
      const token = localStorage.getItem('token');
      const newState = !marketActive;
      
      const response = await axios.post(
        'http://localhost:5000/api/market/control',
        { is_active: newState },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMarketActive(newState);
      setSuccessMessage(`Market ${newState ? 'started' : 'stopped'} successfully`);
      setError('');
    } catch (error: any) {
      console.error('Error controlling market:', error);
      setError(error.response?.data?.error || 'Failed to control market');
      setSuccessMessage('');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setNewStock(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAddStock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:5000/api/admin/stocks/add',
        {
          ...newStock,
          current_price: parseFloat(newStock.current_price)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setSuccessMessage('Stock added successfully');
      setError('');
      // Reset form
      setNewStock({
        symbol: '',
        name: '',
        current_price: ''
      });
    } catch (error: any) {
      console.error('Error adding stock:', error);
      setError(error.response?.data?.error || 'Failed to add stock');
      setSuccessMessage('');
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Admin Dashboard
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {successMessage && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {successMessage}
          </Alert>
        )}

        <Box sx={{ mt: 3, mb: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Market Status: {marketActive ? 'Active' : 'Closed'}
          </Typography>
          <Button
            variant="contained"
            color={marketActive ? 'error' : 'success'}
            onClick={handleMarketControl}
            sx={{ mt: 2 }}
          >
            {marketActive ? 'Stop Market' : 'Start Market'}
          </Button>
        </Box>

        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Add New Stock
          </Typography>
          <form onSubmit={handleAddStock}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Symbol"
                  name="symbol"
                  value={newStock.symbol}
                  onChange={handleInputChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Name"
                  name="name"
                  value={newStock.name}
                  onChange={handleInputChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Initial Price"
                  name="current_price"
                  type="number"
                  value={newStock.current_price}
                  onChange={handleInputChange}
                  margin="normal"
                  inputProps={{ min: "0", step: "0.01" }}
                />
              </Grid>
             
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Add Stock
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>

        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
          Leaderboard
        </Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Rank</TableCell>
                <TableCell>User</TableCell>
                <TableCell align="right">Total Value ($)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {leaderboard.map((entry, index) => (
                <TableRow key={entry.user_id}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>{entry.email}</TableCell>
                  <TableCell align="right">
                    {entry.total_value.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Container>
  );
};

export default AdminDashboard;
