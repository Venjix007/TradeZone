import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Box,
  Grid,
} from '@mui/material';
import axios from 'axios';

interface StockHolding {
  stock_id: string;
  stock_name: string;
  stock_symbol: string;
  quantity: number;
  current_price: number;
  total_value: number;
}

interface UserProfile {
  balance: number;
  total_portfolio_value: number;
}

const Portfolio = () => {
  const [holdings, setHoldings] = useState<StockHolding[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const [holdingsResponse, profileResponse] = await Promise.all([
        axios.get('http://localhost:5000/api/portfolio/holdings'),
        axios.get('http://localhost:5000/api/portfolio/profile'),
      ]);

      setHoldings(holdingsResponse.data);
      setProfile(profileResponse.data);
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    }
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Portfolio
      </Typography>

      {profile && (
        <Box sx={{ mb: 4 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Summary
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography color="textSecondary">Cash Balance</Typography>
                <Typography variant="h5">${profile.balance.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography color="textSecondary">Total Portfolio Value</Typography>
                <Typography variant="h5">
                  ${profile.total_portfolio_value.toFixed(2)}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Stock</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">Total Value</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {holdings.map((holding) => (
              <TableRow key={holding.stock_id}>
                <TableCell>{holding.stock_name}</TableCell>
                <TableCell>{holding.stock_symbol}</TableCell>
                <TableCell align="right">{holding.quantity}</TableCell>
                <TableCell align="right">
                  ${holding.current_price.toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  ${holding.total_value.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default Portfolio;
