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
  IconButton,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  Alert
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from 'axios';

const MenuItems = () => {
  const [products, setProducts] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    selling_price: '',
    category: '',
    ingredients: []
  });

  const categories = ['Hot Coffee', 'Iced Coffee', 'Tea', 'Pastries', 'Other'];
  
  const units = [
    { value: 'g', label: 'Grams (g)', baseUnit: 'g' },
    { value: 'kg', label: 'Kilograms (kg)', baseUnit: 'g' },
    { value: 'ml', label: 'Milliliters (ml)', baseUnit: 'ml' },
    { value: 'l', label: 'Liters (l)', baseUnit: 'ml' },
    { value: 'pcs', label: 'Pieces', baseUnit: 'pcs' }
  ];

  useEffect(() => {
    fetchProducts();
    fetchIngredients();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchIngredients = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/ingredients');
      setIngredients(response.data);
    } catch (error) {
      console.error('Error fetching ingredients:', error);
    }
  };

  const handleOpen = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name,
        description: product.description || '',
        selling_price: product.selling_price.toString(),
        category: product.category,
        ingredients: product.ingredients.map(ing => ({
          ingredient_id: ing.ingredient_id,
          quantity: ing.quantity,
          unit: ing.unit
        }))
      });
    } else {
      setEditingProduct(null);
      setFormData({
        name: '',
        description: '',
        selling_price: '',
        category: '',
        ingredients: []
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingProduct(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAddIngredient = () => {
    setFormData(prev => ({
      ...prev,
      ingredients: [
        ...prev.ingredients,
        { ingredient_id: '', quantity: '', unit: 'g' }
      ]
    }));
  };

  const handleRemoveIngredient = (index) => {
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.filter((_, i) => i !== index)
    }));
  };

  const handleIngredientChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.map((ing, i) => {
        if (i === index) {
          if (field === 'ingredient_id') {
            // When ingredient is selected, set its default unit
            const selectedIngredient = ingredients.find(i => i.id === parseInt(value));
            return {
              ...ing,
              [field]: parseInt(value),
              unit: selectedIngredient ? selectedIngredient.stock_unit : 'g'
            };
          }
          return { ...ing, [field]: value };
        }
        return ing;
      })
    }));
  };

  const getCompatibleUnits = (ingredientId) => {
    const ingredient = ingredients.find(i => i.id === parseInt(ingredientId));
    if (!ingredient) return units;
    
    const baseUnit = ingredient.stock_unit === 'kg' ? 'g' : 
                    ingredient.stock_unit === 'l' ? 'ml' : 
                    ingredient.stock_unit;
    
    return units.filter(u => u.baseUnit === baseUnit);
  };

  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        selling_price: parseFloat(formData.selling_price),
        ingredients: formData.ingredients.map(ing => ({
          ingredient_id: ing.ingredient_id,
          quantity: parseFloat(ing.quantity),
          unit: ing.unit
        }))
      };

      if (editingProduct) {
        await axios.put(`http://localhost:5001/api/products/${editingProduct.id}`, data);
      } else {
        await axios.post('http://localhost:5001/api/products', data);
      }

      handleClose();
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await axios.delete(`http://localhost:5001/api/products/${id}`);
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Menu Items</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpen()}
        >
          Add Menu Item
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Ingredients</TableCell>
              <TableCell>Cost</TableCell>
              <TableCell>Selling Price</TableCell>
              <TableCell>Profit</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>{product.name}</TableCell>
                <TableCell>{product.category}</TableCell>
                <TableCell>{product.description}</TableCell>
                <TableCell>
                  {product.ingredients.map((ing, index) => (
                    <Chip
                      key={index}
                      label={`${ing.ingredient_name}: ${ing.quantity} ${ing.unit}`}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </TableCell>
                <TableCell>฿{product.total_cost.toLocaleString('th-TH', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell>฿{product.selling_price.toLocaleString('th-TH', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell>
                  <Box>
                    <Typography>
                      ฿{(product.profit?.amount || 0).toLocaleString('th-TH', { minimumFractionDigits: 2 })}
                    </Typography>
                    <Typography 
                      variant="caption" 
                      color={(product.profit?.percentage || 0) >= 30 ? 'success.main' : 'warning.main'}
                    >
                      ({(product.profit?.percentage || 0).toFixed(1)}%)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleOpen(product)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(product.id)} size="small">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>{editingProduct ? 'Edit Menu Item' : 'Add Menu Item'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  label="Category"
                >
                  {categories.map((category) => (
                    <MenuItem key={category} value={category}>
                      {category}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Selling Price"
                name="selling_price"
                value={formData.selling_price}
                onChange={handleInputChange}
                type="number"
                InputProps={{
                  startAdornment: '฿'
                }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mb: 2 }}>Ingredients</Typography>
              <List>
                {formData.ingredients.map((ing, index) => (
                  <ListItem key={index} sx={{ border: 1, borderColor: 'grey.300', borderRadius: 1, mb: 1 }}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={4}>
                        <FormControl fullWidth>
                          <InputLabel>Ingredient</InputLabel>
                          <Select
                            value={ing.ingredient_id}
                            onChange={(e) => handleIngredientChange(index, 'ingredient_id', e.target.value)}
                            label="Ingredient"
                          >
                            {ingredients.map((ingredient) => (
                              <MenuItem key={ingredient.id} value={ingredient.id}>
                                {ingredient.name}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          fullWidth
                          label="Quantity"
                          value={ing.quantity}
                          onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                          type="number"
                        />
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <FormControl fullWidth>
                          <InputLabel>Unit</InputLabel>
                          <Select
                            value={ing.unit}
                            onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                            label="Unit"
                          >
                            {getCompatibleUnits(ing.ingredient_id).map((unit) => (
                              <MenuItem key={unit.value} value={unit.value}>
                                {unit.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={2}>
                        <IconButton onClick={() => handleRemoveIngredient(index)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                  </ListItem>
                ))}
              </List>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleAddIngredient}
                sx={{ mt: 1 }}
              >
                Add Ingredient
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingProduct ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MenuItems;
