import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Order {
  id: string;
  stock_symbol: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  status: 'pending' | 'completed' | 'cancelled';
  created_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`orders-tabpanel-${index}`}
      aria-labelledby={`orders-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Orders = () => {
  const [value, setValue] = useState(0);
  const [orders, setOrders] = useState<Order[]>([]);
  const { user } = useAuth();

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/orders', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const filterOrdersByStatus = (status: 'pending' | 'completed' | 'cancelled') => {
    return orders.filter(order => order.status === status);
  };

  const renderOrdersTable = (filteredOrders: Order[]) => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Stock</TableCell>
            <TableCell>Type</TableCell>
            <TableCell align="right">Quantity</TableCell>
            <TableCell align="right">Price</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Date</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredOrders.map((order) => (
            <TableRow key={order.id}>
              <TableCell>{order.stock_symbol}</TableCell>
              <TableCell>{order.type}</TableCell>
              <TableCell align="right">{order.quantity}</TableCell>
              <TableCell align="right">${order.price.toFixed(2)}</TableCell>
              <TableCell>{order.status}</TableCell>
              <TableCell>
                {new Date(order.created_at).toLocaleDateString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Container>
      <Typography variant="h4" gutterBottom sx={{ mt: 4 }}>
        My Orders
      </Typography>
      <Paper sx={{ width: '100%', mt: 3 }}>
        <Tabs
          value={value}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab label="Pending Orders" />
          <Tab label="Completed Orders" />
          <Tab label="Cancelled Orders" />
        </Tabs>

        <TabPanel value={value} index={0}>
          {renderOrdersTable(filterOrdersByStatus('pending'))}
        </TabPanel>
        <TabPanel value={value} index={1}>
          {renderOrdersTable(filterOrdersByStatus('completed'))}
        </TabPanel>
        <TabPanel value={value} index={2}>
          {renderOrdersTable(filterOrdersByStatus('cancelled'))}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default Orders;
