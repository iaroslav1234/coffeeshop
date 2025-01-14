import React, { useState, useEffect } from 'react';
import { Grid, Paper, Typography, Alert, Box } from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

const Dashboard = () => {
  const [lowStockAlerts, setLowStockAlerts] = useState([]);
  const [financeOverview, setFinanceOverview] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch low stock alerts
        const alertsResponse = await axios.get(`${API_URL}/low-stock-alerts`);
        setLowStockAlerts(alertsResponse.data);

        // Fetch finance overview
        const financeResponse = await axios.get(`${API_URL}/finance`);
        setFinanceOverview(financeResponse.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Grid container spacing={3}>
        {/* Low Stock Alerts */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Low Stock Alerts
            </Typography>
            {lowStockAlerts.map((alert) => (
              <Alert 
                key={alert.id} 
                severity="warning" 
                sx={{ mb: 1 }}
              >
                {alert.name} is running low! Current stock: {alert.current_stock} {alert.unit}
              </Alert>
            ))}
            {lowStockAlerts.length === 0 && (
              <Typography color="text.secondary">
                No low stock alerts at the moment
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Financial Overview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Financial Overview
            </Typography>
            {financeOverview && (
              <Box>
                <Typography>Current Balance: ฿{financeOverview.current_balance.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Typography>
                <Typography>Total Income: ฿{financeOverview.total_income.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Typography>
                <Typography>Total Expenses: ฿{financeOverview.total_expenses.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Stats
            </Typography>
            <Typography>
              Welcome to your Coffee Shop Dashboard! Here you can monitor your shop's performance
              and get quick access to important information.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
