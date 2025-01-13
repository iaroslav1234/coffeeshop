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
      main: '#795548', // Coffee brown
    },
    secondary: {
      main: '#4CAF50', // Green for profit indicators
    },
    background: {
      default: '#f5f5f5',
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
