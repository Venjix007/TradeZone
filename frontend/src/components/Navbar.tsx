import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import { AccountCircle, Brightness4, Brightness7 } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const Navbar = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
    navigate('/login');
  };

  if (!user) {
    return null;
  }

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Chesa Stock Exchange
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button color="inherit" onClick={() => navigate('/')}>
            Market
          </Button>
          <Button color="inherit" onClick={() => navigate('/portfolio')}>
            Portfolio
          </Button>
          <Button color="inherit" onClick={() => navigate('/orders')}>
            Orders
          </Button>
          <Button color="inherit" onClick={() => navigate('/news')}>
            News
          </Button>
          {user.role === 'admin' && (
            <Button color="inherit" onClick={() => navigate('/admin')}>
              Admin
            </Button>
          )}
          <Tooltip title={`Switch to ${isDarkMode ? 'Light' : 'Dark'} Mode`}>
            <IconButton
              size="large"
              onClick={toggleTheme}
              color="inherit"
              sx={{ ml: 1 }}
            >
              {isDarkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Tooltip>
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenu}
            color="inherit"
          >
            <AccountCircle />
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={handleLogout}>Logout</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
