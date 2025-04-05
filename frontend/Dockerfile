# Use Node.js base image
FROM node:20.11.0-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY portfolio-website/package*.json ./

# Install dependencies
RUN npm install
RUN npm install -g @angular/cli

# Copy project files
COPY portfolio-website/ .

# Expose port
EXPOSE 4200

# Disable Vite error overlay and run in production mode
ENV VITE_DISABLE_ERROR_OVERLAY=true
CMD ["ng", "serve", "--configuration", "production", "--port", "4200", "--host", "0.0.0.0", "--disable-host-check"]