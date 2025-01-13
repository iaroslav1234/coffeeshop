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
  MenuItem,
  Alert,
  IconButton
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from 'axios';

const StockUpdates = () => {
  const [stockUpdates, setStockUpdates] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [open, setOpen] = useState(false);
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'success' });
  const [formData, setFormData] = useState({
    ingredient_id: '',
    quantity: '',
    cost_per_unit: '',
    notes: ''
  });

  useEffect(() => {
    fetchStockUpdates();
    fetchIngredients();
  }, []);

  const fetchStockUpdates = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/stock-updates');
      setStockUpdates(response.data);
    } catch (error) {
      console.error('Error fetching stock updates:', error);
      showAlert('Error fetching stock updates', 'error');
    }
  };

  const fetchIngredients = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/ingredients');
      setIngredients(response.data);
    } catch (error) {
      console.error('Error fetching ingredients:', error);
      showAlert('Error fetching ingredients', 'error');
    }
  };

  const handleOpen = () => {
    setOpen(true);
    setFormData({
      ingredient_id: '',
      quantity: '',
      cost_per_unit: '',
      notes: ''
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

  const showAlert = (message, severity = 'success') => {
    setAlert({ show: true, message, severity });
    setTimeout(() => setAlert({ show: false, message: '', severity: 'success' }), 3000);
  };

  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        quantity: parseFloat(formData.quantity),
        cost_per_unit: parseFloat(formData.cost_per_unit)
      };

      await axios.post('http://localhost:5001/api/stock-updates', data);
      showAlert('Stock update recorded successfully');
      handleClose();
      fetchStockUpdates();
    } catch (error) {
      console.error('Error saving stock update:', error);
      showAlert('Error saving stock update', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this stock update? This will revert the inventory changes.')) {
      try {
        await axios.delete(`http://localhost:5001/api/stock-updates/${id}`);
        showAlert('Stock update deleted successfully');
        fetchStockUpdates();
      } catch (error) {
        console.error('Error deleting stock update:', error);
        showAlert('Error deleting stock update', 'error');
      }
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Stock Updates</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          Add Stock Update
        </Button>
      </Box>

      {alert.show && (
        <Alert severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Ingredient</TableCell>
              <TableCell>Quantity</TableCell>
              <TableCell>Cost per Unit</TableCell>
              <TableCell>Total Cost</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stockUpdates.map((update) => (
              <TableRow key={update.id}>
                <TableCell>{new Date(update.date).toLocaleDateString()}</TableCell>
                <TableCell>{update.ingredient_name}</TableCell>
                <TableCell>{update.quantity} {update.unit}</TableCell>
                <TableCell>฿{update.cost_per_unit.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                <TableCell>฿{update.total_cost.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                <TableCell>{update.notes}</TableCell>
                <TableCell>
                  <IconButton onClick={() => handleDelete(update.id)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Add Stock Update</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              select
              name="ingredient_id"
              label="Select Ingredient"
              value={formData.ingredient_id}
              onChange={handleInputChange}
              fullWidth
            >
              {ingredients.map((ingredient) => (
                <MenuItem key={ingredient.id} value={ingredient.id}>
                  {ingredient.name} (Current: {ingredient.current_stock} {ingredient.unit})
                </MenuItem>
              ))}
            </TextField>
            <TextField
              name="quantity"
              label="Quantity"
              type="number"
              value={formData.quantity}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              name="cost_per_unit"
              label="Cost per Unit (฿)"
              type="number"
              value={formData.cost_per_unit}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              name="notes"
              label="Notes"
              multiline
              rows={2}
              value={formData.notes}
              onChange={handleInputChange}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Add Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StockUpdates;
