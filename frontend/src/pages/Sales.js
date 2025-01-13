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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  IconButton,
  Stack,
  Alert
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
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

const Sales = () => {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [open, setOpen] = useState(false);
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    product_id: '',
    quantity: 1
  });

  useEffect(() => {
    fetchSales();
    fetchProducts();
  }, []);

  const fetchSales = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/sales');
      setSales(response.data);
    } catch (error) {
      console.error('Error fetching sales:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    setFormData({
      date: new Date().toISOString().split('T')[0],
      product_id: '',
      quantity: 1
    });
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        date: new Date(formData.date).toISOString()
      };
      await axios.post('http://localhost:5001/api/sales', data);
      handleClose();
      fetchSales();
    } catch (error) {
      console.error('Error creating sale:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this sale?')) {
      try {
        await axios.delete(`http://localhost:5001/api/sales/${id}`);
        fetchSales();
      } catch (error) {
        console.error('Error deleting sale:', error);
      }
    }
  };

  const getFilteredSales = () => {
    if (!filterStartDate && !filterEndDate) return sales;

    return sales.filter(sale => {
      const saleDate = new Date(sale.date);
      if (filterStartDate && filterEndDate) {
        return saleDate >= new Date(filterStartDate) && saleDate <= new Date(filterEndDate);
      } else if (filterStartDate) {
        return saleDate >= new Date(filterStartDate);
      } else {
        return saleDate <= new Date(filterEndDate);
      }
    });
  };

  const calculateTotalRevenue = (sales) => {
    return sales.reduce((sum, sale) => sum + sale.revenue, 0);
  };

  const calculateTotalProfit = (sales) => {
    return sales.reduce((sum, sale) => sum + sale.profit, 0);
  };

  const filteredSales = getFilteredSales();

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Sales</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          Add Sale
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              type="date"
              label="Start Date"
              value={filterStartDate}
              onChange={(e) => setFilterStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              type="date"
              label="End Date"
              value={filterEndDate}
              onChange={(e) => setFilterEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Stack spacing={1}>
              <Typography variant="subtitle2">
                Total Revenue: ฿{calculateTotalRevenue(filteredSales).toLocaleString('th-TH', { minimumFractionDigits: 2 })}
              </Typography>
              <Typography variant="subtitle2">
                Total Profit: ฿{calculateTotalProfit(filteredSales).toLocaleString('th-TH', { minimumFractionDigits: 2 })}
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Product</TableCell>
              <TableCell>Quantity</TableCell>
              <TableCell>Cost</TableCell>
              <TableCell>Revenue</TableCell>
              <TableCell>Profit</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredSales.map((sale) => (
              <TableRow key={sale.id}>
                <TableCell>{formatDate(sale.date)}</TableCell>
                <TableCell>{sale.product_name}</TableCell>
                <TableCell>{sale.quantity}</TableCell>
                <TableCell>฿{sale.cost.toLocaleString('th-TH', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell>฿{sale.revenue.toLocaleString('th-TH', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell>฿{sale.profit.toLocaleString('th-TH', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell>
                  <IconButton onClick={() => handleDelete(sale.id)} size="small">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Add Sale</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="date"
                label="Date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Product</InputLabel>
                <Select
                  name="product_id"
                  value={formData.product_id}
                  onChange={handleInputChange}
                  label="Product"
                >
                  {products.map((product) => (
                    <MenuItem key={product.id} value={product.id}>
                      {product.name} - ฿{product.selling_price}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Quantity"
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleInputChange}
                inputProps={{ min: 1 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Add Sale
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Sales;
