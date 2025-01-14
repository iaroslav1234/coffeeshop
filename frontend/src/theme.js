import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      light: '#9575cd',
      main: '#7c4dff',
      dark: '#6c3fff',
      contrastText: '#fff',
    },
    secondary: {
      light: '#e0f7fa',
      main: '#f3e5f5',
      dark: '#e1bee7',
      contrastText: '#666',
    },
    background: {
      default: '#e0f7fa',
      paper: 'rgba(255, 255, 255, 0.95)',
    },
    text: {
      primary: '#7c4dff',
      secondary: '#9575cd',
    },
    error: {
      main: '#ff80ab',
      light: 'rgba(255, 128, 171, 0.1)',
    },
  },
  typography: {
    fontFamily: '"Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#7c4dff',
    },
    h5: {
      fontWeight: 600,
      color: '#7c4dff',
    },
    h6: {
      fontWeight: 600,
      color: '#7c4dff',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '50px',
          textTransform: 'none',
          fontWeight: 'bold',
        },
        contained: {
          background: 'linear-gradient(45deg, #9575cd, #7c4dff)',
          '&:hover': {
            background: 'linear-gradient(45deg, #7c4dff, #6c3fff)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          boxShadow: '0 8px 32px 0 rgba(147, 147, 247, 0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          boxShadow: '0 8px 32px 0 rgba(147, 147, 247, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '50px',
            '& fieldset': {
              borderColor: '#e1bee7',
            },
            '&:hover fieldset': {
              borderColor: '#9575cd',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#7c4dff',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '50px',
          '&:hover': {
            transform: 'scale(1.05)',
            transition: 'transform 0.2s',
          },
        },
      },
    },
  },
});

export default theme;
