import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Typography,
  Box,
  Alert,
  Snackbar,
  Divider,
  Grid
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';

function Inventory() {
  const [ingredients, setIngredients] = useState([]);
  const [categories, setCategories] = useState([]);
  const [openIngredientDialog, setOpenIngredientDialog] = useState(false);
  const [openCategoryDialog, setOpenCategoryDialog] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [ingredientForm, setIngredientForm] = useState({
    name: '',
    category_id: '',
    current_stock: '',
    stock_unit: 'kg',
    min_threshold: '',
    threshold_unit: 'g',
    cost_per_unit: '',
  });
  const [categoryForm, setCategoryForm] = useState({
    name: '',
  });

  const units = [
    { value: 'g', label: 'Grams (g)', baseUnit: 'g' },
    { value: 'kg', label: 'Kilograms (kg)', baseUnit: 'g' },
    { value: 'ml', label: 'Milliliters (ml)', baseUnit: 'ml' },
    { value: 'l', label: 'Liters (l)', baseUnit: 'ml' },
    { value: 'pcs', label: 'Pieces', baseUnit: 'pcs' },
    { value: 'bottles', label: 'Bottles', baseUnit: 'bottles' },
    { value: 'packs', label: 'Packs', baseUnit: 'packs' }
  ];

  const getCompatibleUnits = (unit) => {
    if (!unit) return units;
    const selectedUnit = units.find(u => u.value === unit);
    if (!selectedUnit) return units;
    return units.filter(u => u.baseUnit === selectedUnit.baseUnit);
  };

  useEffect(() => {
    fetchIngredients();
    fetchCategories();
  }, []);

  const fetchIngredients = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/ingredients');
      setIngredients(response.data);
    } catch (error) {
      showSnackbar('Error fetching ingredients', 'error');
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/ingredient-categories');
      setCategories(response.data);
    } catch (error) {
      showSnackbar('Error fetching categories', 'error');
    }
  };

  const handleOpenIngredientDialog = (ingredient = null) => {
    if (ingredient) {
      setSelectedIngredient(ingredient);
      setIngredientForm({
        name: ingredient.name,
        category_id: ingredient.category_id,
        current_stock: ingredient.current_stock,
        stock_unit: ingredient.stock_unit,
        min_threshold: ingredient.min_threshold,
        threshold_unit: ingredient.threshold_unit,
        cost_per_unit: ingredient.cost_per_unit,
      });
    } else {
      setSelectedIngredient(null);
      setIngredientForm({
        name: '',
        category_id: '',
        current_stock: '',
        stock_unit: 'kg',
        min_threshold: '',
        threshold_unit: 'g',
        cost_per_unit: '',
      });
    }
    setOpenIngredientDialog(true);
  };

  const handleOpenCategoryDialog = (category = null) => {
    if (category) {
      setSelectedCategory(category);
      setCategoryForm({ name: category.name });
    } else {
      setSelectedCategory(null);
      setCategoryForm({ name: '' });
    }
    setOpenCategoryDialog(true);
  };

  const handleCloseIngredientDialog = () => {
    setOpenIngredientDialog(false);
    setSelectedIngredient(null);
    setIngredientForm({
      name: '',
      category_id: '',
      current_stock: '',
      stock_unit: 'kg',
      min_threshold: '',
      threshold_unit: 'g',
      cost_per_unit: '',
    });
  };

  const handleCloseCategoryDialog = () => {
    setOpenCategoryDialog(false);
    setSelectedCategory(null);
    setCategoryForm({ name: '' });
  };

  const handleIngredientSubmit = async () => {
    try {
      if (selectedIngredient) {
        await axios.put(`http://localhost:5001/api/ingredients/${selectedIngredient.id}`, ingredientForm);
        showSnackbar('Ingredient updated successfully');
      } else {
        await axios.post('http://localhost:5001/api/ingredients', ingredientForm);
        showSnackbar('Ingredient added successfully');
      }
      handleCloseIngredientDialog();
      fetchIngredients();
    } catch (error) {
      showSnackbar(error.response?.data?.message || 'Error saving ingredient', 'error');
    }
  };

  const handleCategorySubmit = async () => {
    try {
      if (selectedCategory) {
        await axios.put(`http://localhost:5001/api/ingredient-categories/${selectedCategory.id}`, categoryForm);
        showSnackbar('Category updated successfully');
      } else {
        await axios.post('http://localhost:5001/api/ingredient-categories', categoryForm);
        showSnackbar('Category added successfully');
      }
      handleCloseCategoryDialog();
      fetchCategories();
    } catch (error) {
      showSnackbar(error.response?.data?.message || 'Error saving category', 'error');
    }
  };

  const handleDeleteIngredient = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/api/ingredients/${id}`);
      showSnackbar('Ingredient deleted successfully');
      fetchIngredients();
    } catch (error) {
      showSnackbar(error.response?.data?.message || 'Error deleting ingredient', 'error');
    }
  };

  const handleDeleteCategory = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/api/ingredient-categories/${id}`);
      showSnackbar('Category deleted successfully');
      fetchCategories();
      fetchIngredients(); // Refresh ingredients as their categories might have changed
    } catch (error) {
      showSnackbar(error.response?.data?.message || 'Error deleting category', 'error');
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Group ingredients by category
  const groupedIngredients = ingredients.reduce((acc, ingredient) => {
    const categoryName = ingredient.category_name;
    if (!acc[categoryName]) {
      acc[categoryName] = [];
    }
    acc[categoryName].push(ingredient);
    return acc;
  }, {});

  return (
    <div style={{ padding: '20px' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Inventory Management</Typography>
        <Box>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => handleOpenIngredientDialog()}
            style={{ marginRight: '10px' }}
          >
            Add Ingredient
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<AddIcon />}
            onClick={() => handleOpenCategoryDialog()}
          >
            Manage Categories
          </Button>
        </Box>
      </Box>

      {/* Categories Dialog */}
      <Dialog open={openCategoryDialog} onClose={handleCloseCategoryDialog}>
        <DialogTitle>{selectedCategory ? 'Edit Category' : 'Add Category'}</DialogTitle>
        <DialogContent>
          <Box mb={2}>
            <TextField
              autoFocus
              margin="dense"
              label="Category Name"
              fullWidth
              value={categoryForm.name}
              onChange={(e) => setCategoryForm({ name: e.target.value })}
            />
          </Box>
          {categories.length > 0 && (
            <Box mt={2}>
              <Typography variant="h6" gutterBottom>
                Existing Categories
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableBody>
                    {categories.map((category) => (
                      <TableRow key={category.id}>
                        <TableCell>{category.name}</TableCell>
                        <TableCell align="right">
                          <IconButton
                            color="primary"
                            onClick={() => handleOpenCategoryDialog(category)}
                            size="small"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            color="error"
                            onClick={() => handleDeleteCategory(category.id)}
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCategoryDialog}>Cancel</Button>
          <Button onClick={handleCategorySubmit} color="primary">
            {selectedCategory ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Ingredient Dialog */}
      <Dialog open={openIngredientDialog} onClose={handleCloseIngredientDialog}>
        <DialogTitle>{selectedIngredient ? 'Edit Ingredient' : 'Add Ingredient'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              name="name"
              label="Name"
              value={ingredientForm.name}
              onChange={(e) => setIngredientForm({ ...ingredientForm, name: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={ingredientForm.category_id}
                onChange={(e) => setIngredientForm({ ...ingredientForm, category_id: e.target.value })}
                label="Category"
              >
                {categories.map((category) => (
                  <MenuItem key={category.id} value={category.id}>
                    {category.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Grid container spacing={2}>
              <Grid item xs={8}>
                <TextField
                  name="current_stock"
                  label="Current Stock"
                  type="number"
                  value={ingredientForm.current_stock}
                  onChange={(e) => setIngredientForm({ ...ingredientForm, current_stock: e.target.value })}
                  fullWidth
                  InputProps={{
                    endAdornment: <Typography color="textSecondary">{ingredientForm.stock_unit}</Typography>
                  }}
                />
              </Grid>
              <Grid item xs={4}>
                <FormControl fullWidth>
                  <InputLabel>Stock Unit</InputLabel>
                  <Select
                    name="stock_unit"
                    value={ingredientForm.stock_unit}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, stock_unit: e.target.value })}
                    label="Stock Unit"
                  >
                    {units.map((unit) => (
                      <MenuItem key={unit.value} value={unit.value}>
                        {unit.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            <Grid container spacing={2}>
              <Grid item xs={8}>
                <TextField
                  name="min_threshold"
                  label="Minimum Stock Alert Threshold"
                  type="number"
                  value={ingredientForm.min_threshold}
                  onChange={(e) => setIngredientForm({ ...ingredientForm, min_threshold: e.target.value })}
                  fullWidth
                  helperText={`Alert will trigger when stock falls below this amount (in ${
                    units.find(u => u.value === ingredientForm.threshold_unit)?.label || ingredientForm.threshold_unit
                  })`}
                  InputProps={{
                    endAdornment: <Typography color="textSecondary">{ingredientForm.threshold_unit}</Typography>
                  }}
                />
              </Grid>
              <Grid item xs={4}>
                <FormControl fullWidth>
                  <InputLabel>Threshold Unit</InputLabel>
                  <Select
                    name="threshold_unit"
                    value={ingredientForm.threshold_unit}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, threshold_unit: e.target.value })}
                    label="Threshold Unit"
                  >
                    {getCompatibleUnits(ingredientForm.stock_unit).map((unit) => (
                      <MenuItem key={unit.value} value={unit.value}>
                        {unit.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            <TextField
              name="cost_per_unit"
              label={`Cost per ${ingredientForm.stock_unit} (฿)`}
              type="number"
              value={ingredientForm.cost_per_unit}
              onChange={(e) => setIngredientForm({ ...ingredientForm, cost_per_unit: e.target.value })}
              fullWidth
              helperText={`Enter the cost for 1 ${ingredientForm.stock_unit}`}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseIngredientDialog}>Cancel</Button>
          <Button onClick={handleIngredientSubmit} variant="contained">
            {selectedIngredient ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Ingredients Tables by Category */}
      {Object.entries(groupedIngredients).map(([categoryName, categoryIngredients]) => (
        <Box key={categoryName} mb={4}>
          <Typography variant="h5" gutterBottom style={{ backgroundColor: '#f5f5f5', padding: '10px' }}>
            {categoryName}
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell align="right">Current Stock</TableCell>
                  <TableCell align="right">Min Threshold</TableCell>
                  <TableCell align="right">Cost per Unit</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {categoryIngredients.map((ingredient) => (
                  <TableRow
                    key={ingredient.id}
                    style={{
                      backgroundColor: ingredient.low_stock ? '#fff3f3' : 'inherit',
                    }}
                  >
                    <TableCell>{ingredient.name}</TableCell>
                    <TableCell align="right">
                      {ingredient.current_stock} {ingredient.stock_unit}
                    </TableCell>
                    <TableCell align="right">
                      {ingredient.min_threshold} {ingredient.threshold_unit}
                    </TableCell>
                    <TableCell align="right">
                      ${ingredient.cost_per_unit}/{ingredient.cost_unit}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenIngredientDialog(ingredient)}
                        size="small"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteIngredient(ingredient.id)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      ))}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </div>
  );
}

export default Inventory;
