import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Grid,
  IconButton,
  Stack,
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  TextField,
  InputAdornment,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  ShoppingCart as CartIcon
} from '@mui/icons-material';
import axios from 'axios';

const formatDate = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('th-TH', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('th-TH', {
    style: 'currency',
    currency: 'THB'
  }).format(amount);
};

const Sales = () => {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [cart, setCart] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    fetchSales();
    fetchProducts();
  }, []);

  const fetchSales = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/sales');
      setSales(response.data);
    } catch (error) {
      showSnackbar('Error fetching sales', 'error');
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/products');
      setProducts(response.data);
      
      // Extract unique categories
      const uniqueCategories = [...new Set(response.data.map(product => product.category))];
      setCategories(uniqueCategories);
    } catch (error) {
      showSnackbar('Error fetching products', 'error');
    }
  };

  const handleAddToCart = (product) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product_id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prevCart, {
        product_id: product.id,
        name: product.name,
        price: product.selling_price,
        quantity: 1
      }];
    });
    showSnackbar('Added to cart');
  };

  const handleUpdateQuantity = (productId, change) => {
    setCart(prevCart => {
      return prevCart.map(item => {
        if (item.product_id === productId) {
          const newQuantity = Math.max(0, item.quantity + change);
          return newQuantity === 0 ? null : { ...item, quantity: newQuantity };
        }
        return item;
      }).filter(Boolean);
    });
  };

  const handleRemoveFromCart = (productId) => {
    setCart(prevCart => prevCart.filter(item => item.product_id !== productId));
    showSnackbar('Removed from cart');
  };

  const handleCheckout = async () => {
    try {
      for (const item of cart) {
        await axios.post('http://localhost:5001/api/sales', {
          product_id: item.product_id,
          quantity: item.quantity,
          date: new Date().toISOString()
        });
      }
      setCart([]);
      fetchSales();
      showSnackbar('Sale completed successfully');
    } catch (error) {
      showSnackbar('Error processing sale', 'error');
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const filteredProducts = products
    .filter(product => 
      (selectedCategory === 'all' || product.category === selectedCategory) &&
      (searchQuery === '' || product.name.toLowerCase().includes(searchQuery.toLowerCase()))
    );

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  return (
    <Box 
      p={3} 
      sx={{
        background: 'linear-gradient(135deg, #e0f7fa 0%, #f3e5f5 100%)',
        minHeight: '100vh'
      }}
    >
      <Grid container spacing={3}>
        {/* Left side - Product Selection */}
        <Grid item xs={12} md={8}>
          <Paper 
            sx={{ 
              p: 2, 
              mb: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              boxShadow: '0 8px 32px 0 rgba(147, 147, 247, 0.1)'
            }}
          >
            <Stack direction="row" spacing={2} alignItems="center" mb={2}>
              <TextField
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ flexGrow: 1 }}
              />
            </Stack>
            
            <Stack direction="row" spacing={1} mb={2} sx={{ overflowX: 'auto', pb: 1 }}>
              <Chip
                label="All"
                onClick={() => setSelectedCategory('all')}
                color={selectedCategory === 'all' ? 'primary' : 'default'}
              />
              {categories.map(category => (
                <Chip
                  key={category}
                  label={category}
                  onClick={() => setSelectedCategory(category)}
                  color={selectedCategory === category ? 'primary' : 'default'}
                />
              ))}
            </Stack>

            <Grid container spacing={2}>
              {filteredProducts.map(product => (
                <Grid item xs={12} sm={6} md={4} key={product.id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      '&:hover': { transform: 'scale(1.02)', transition: 'transform 0.2s' }
                    }}
                    onClick={() => handleAddToCart(product)}
                  >
                    <CardContent>
                      <Typography variant="h6" noWrap>{product.name}</Typography>
                      <Typography color="textSecondary" gutterBottom>{product.category}</Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(product.selling_price)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Right side - Cart */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, position: 'sticky', top: 16 }}>
            <Typography variant="h6" gutterBottom>
              Current Order
            </Typography>
            
            {cart.length === 0 ? (
              <Typography color="textSecondary" align="center" py={4}>
                Cart is empty
              </Typography>
            ) : (
              <>
                {cart.map(item => (
                  <Box key={item.product_id} mb={2}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle1">{item.name}</Typography>
                      <IconButton 
                        size="small" 
                        color="error"
                        onClick={() => handleRemoveFromCart(item.product_id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Stack>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <IconButton 
                          size="small"
                          onClick={() => handleUpdateQuantity(item.product_id, -1)}
                        >
                          <RemoveIcon />
                        </IconButton>
                        <Typography>{item.quantity}</Typography>
                        <IconButton 
                          size="small"
                          onClick={() => handleUpdateQuantity(item.product_id, 1)}
                        >
                          <AddIcon />
                        </IconButton>
                      </Stack>
                      <Typography>
                        {formatCurrency(item.price * item.quantity)}
                      </Typography>
                    </Stack>
                    <Divider sx={{ mt: 1 }} />
                  </Box>
                ))}

                <Stack spacing={2} mt={2}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="h6">Total:</Typography>
                    <Typography variant="h6">{formatCurrency(calculateTotal())}</Typography>
                  </Box>
                  <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    startIcon={<CartIcon />}
                    onClick={handleCheckout}
                    fullWidth
                  >
                    Complete Sale
                  </Button>
                </Stack>
              </>
            )}
          </Paper>
        </Grid>

        {/* Sales History */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Sales
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Product</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sales.slice(0, 5).map((sale) => (
                    <TableRow key={sale.id}>
                      <TableCell>{formatDate(sale.date)}</TableCell>
                      <TableCell>
                        {products.find(p => p.id === sale.product_id)?.name || 'Unknown Product'}
                      </TableCell>
                      <TableCell align="right">{sale.quantity}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(
                          sale.quantity * (products.find(p => p.id === sale.product_id)?.selling_price || 0)
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Sales;
