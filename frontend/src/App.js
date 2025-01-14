import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import StockUpdates from './pages/StockUpdates';
import MenuItems from './pages/MenuItems';
import Sales from './pages/Sales';
import Finance from './pages/Finance';
import Navbar from './components/Navbar';

const theme = createTheme({
  palette: {
    primary: {
      main: '#7c4dff', // Purple instead of brown
      light: '#9575cd',
      dark: '#6c3fff',
    },
    secondary: {
      main: '#4CAF50', // Keep green for profit indicators
    },
    background: {
      default: '#e0f7fa',
      paper: 'rgba(255, 255, 255, 0.95)',
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 8px 32px 0 rgba(147, 147, 247, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        containedPrimary: {
          background: 'linear-gradient(45deg, #9575cd, #7c4dff)',
          '&:hover': {
            background: 'linear-gradient(45deg, #7c4dff, #6c3fff)',
          },
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/stock-updates" element={<StockUpdates />} />
              <Route path="/menu-items" element={<MenuItems />} />
              <Route path="/sales" element={<Sales />} />
              <Route path="/finance" element={<Finance />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
