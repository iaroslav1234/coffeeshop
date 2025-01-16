# Coffee Shop Manager

A comprehensive application for managing your coffee shop's inventory, menu, sales, and finances.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Node.js and npm
- PostgreSQL

### Installation

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

We provide two convenient scripts to start the development servers:

1. Start the backend server:
   ```bash
   cd dev
   ./start-backend.sh
   ```

2. In a new terminal, start the frontend server:
   ```bash
   cd dev
   ./start-frontend.sh
   ```

The application will be available at:
- Frontend: http://localhost:3002
- Backend API: http://localhost:5001

Both servers feature hot-reloading:
- Frontend changes will automatically refresh in your browser
- Backend changes will automatically restart the Flask server

## Features

- **Inventory Management**
  - Track ingredients and supplies
  - Set low stock alerts
  - Record stock updates with cost tracking

- **Menu Management**
  - Create and manage menu items
  - Recipe management with ingredient quantities
  - Automatic cost calculation
  - Track profit margins

- **Sales Tracking** (Coming Soon)
  - Record sales transactions
  - Track popular items
  - Daily/weekly/monthly reports

- **Financial Overview** (Coming Soon)
  - Track revenue and expenses
  - Generate financial reports
  - Profit analysis

## Recent Updates

- Fixed unit conversion and cost calculation issues (Jan 16, 2025)
  - Corrected stock deduction to handle kg/g conversions properly
  - Fixed cost display to show correct prices (60 baht/kg instead of 60,000)
  - Fixed inventory to store exact values without unnecessary conversions
