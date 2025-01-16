import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography
} from '@mui/material';
import axios from 'axios';

const TransactionList = () => {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/cash-transactions');
      console.log('Transactions:', response.data); // Debug log
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
      minimumFractionDigits: 2
    }).format(Math.abs(amount));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('th-TH', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAmountColor = (type, amount) => {
    // Debug log
    console.log('Transaction type:', type, 'Amount:', amount);
    
    if (type === 'sale' || type === 'deposit') {
      return 'success.main';
    }
    return 'error.main';
  };

  const getDisplayAmount = (type, amount) => {
    const prefix = (type === 'sale' || type === 'deposit') ? '+' : '-';
    return `${prefix}${formatCurrency(amount)}`;
  };

  return (
    <TableContainer component={Paper}>
      <Typography variant="h6" sx={{ p: 2 }}>
        Recent Transactions
      </Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Date</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Description</TableCell>
            <TableCell align="right">Amount</TableCell>
            <TableCell align="right">Balance</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.id}>
              <TableCell>{formatDate(transaction.date)}</TableCell>
              <TableCell sx={{ textTransform: 'capitalize' }}>{transaction.type}</TableCell>
              <TableCell>{transaction.notes}</TableCell>
              <TableCell 
                align="right"
                sx={{ 
                  color: getAmountColor(transaction.type, transaction.amount),
                  fontWeight: 'bold'
                }}
              >
                {getDisplayAmount(transaction.type, transaction.amount)}
              </TableCell>
              <TableCell align="right">
                {formatCurrency(transaction.balance_after)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default TransactionList;
