FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY . .

# Expose the port
EXPOSE ${PORT}

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/health || exit 1

# Start the application
CMD ["npm", "start"]
