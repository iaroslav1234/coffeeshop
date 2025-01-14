import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Paper,
  TextField,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon
} from '@mui/icons-material';

const Finance = () => {
  const [period, setPeriod] = useState('daily');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profitData, setProfitData] = useState({
    total_revenue: 0,
    total_cost: 0,
    total_profit: 0,
    data: []
  });

  useEffect(() => {
    fetchProfitData();
  }, [period, selectedDate]);

  const fetchProfitData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`http://localhost:5001/api/finance/profit`, {
        params: {
          period,
          date: selectedDate.toISOString()
        }
      });
      setProfitData(response.data);
    } catch (err) {
      setError('Error fetching financial data');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (event, newPeriod) => {
    if (newPeriod !== null) {
      setPeriod(newPeriod);
    }
  };

  const handlePrevious = () => {
    const newDate = new Date(selectedDate);
    if (period === 'daily') {
      newDate.setDate(newDate.getDate() - 1);
    } else if (period === 'weekly') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    setSelectedDate(newDate);
  };

  const handleNext = () => {
    const newDate = new Date(selectedDate);
    if (period === 'daily') {
      newDate.setDate(newDate.getDate() + 1);
    } else if (period === 'weekly') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setSelectedDate(newDate);
  };

  const handleToday = () => {
    setSelectedDate(new Date());
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    if (period === 'daily') {
      return date.toLocaleTimeString([], { hour: '2-digit' });
    }
    return date.toLocaleDateString();
  };

  const getDateDisplay = () => {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    if (period === 'daily') {
      return selectedDate.toLocaleDateString(undefined, options);
    } else if (period === 'weekly') {
      const weekStart = new Date(selectedDate);
      weekStart.setDate(weekStart.getDate() - weekStart.getDay());
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);
      return `Week of ${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
    } else {
      return selectedDate.toLocaleDateString(undefined, { year: 'numeric', month: 'long' });
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Financial Overview
      </Typography>

      <Stack direction="row" spacing={2} alignItems="center" mb={3}>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={handlePeriodChange}
          aria-label="time period"
        >
          <ToggleButton value="daily" aria-label="daily">
            Daily
          </ToggleButton>
          <ToggleButton value="weekly" aria-label="weekly">
            Weekly
          </ToggleButton>
          <ToggleButton value="monthly" aria-label="monthly">
            Monthly
          </ToggleButton>
        </ToggleButtonGroup>

        <Stack direction="row" spacing={1} alignItems="center">
          <Tooltip title="Previous">
            <IconButton onClick={handlePrevious}>
              <ChevronLeftIcon />
            </IconButton>
          </Tooltip>
          
          <Typography variant="h6" sx={{ minWidth: period === 'weekly' ? '300px' : '200px', textAlign: 'center' }}>
            {getDateDisplay()}
          </Typography>
          
          <Tooltip title="Next">
            <IconButton onClick={handleNext}>
              <ChevronRightIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Today">
            <IconButton onClick={handleToday}>
              <TodayIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 2, bgcolor: '#fff3f3' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : (
        <>
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Revenue
                  </Typography>
                  <Typography variant="h5" component="div">
                    {formatCurrency(profitData.total_revenue)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Cost
                  </Typography>
                  <Typography variant="h5" component="div">
                    {formatCurrency(profitData.total_cost)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Net Profit
                  </Typography>
                  <Typography 
                    variant="h5" 
                    component="div"
                    color={profitData.total_profit >= 0 ? 'success.main' : 'error.main'}
                  >
                    {formatCurrency(profitData.total_profit)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Paper sx={{ p: 3, height: '400px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={profitData.data}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                />
                <YAxis />
                <ChartTooltip 
                  formatter={(value) => formatCurrency(value)}
                  labelFormatter={formatDate}
                />
                <Legend />
                <Bar dataKey="revenue" name="Revenue" fill="#4caf50" />
                <Bar dataKey="cost" name="Cost" fill="#f44336" />
                <Bar dataKey="profit" name="Profit" fill="#2196f3" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default Finance;
