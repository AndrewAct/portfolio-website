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

#CMD VITE_DISABLE_ERROR_OVERLAY=true ng serve --port 4200 --host 0.0.0.0 --disable-host-check
# Disable Vite error overlay
ENV VITE_DISABLE_ERROR_OVERLAY=true
CMD ["ng", "serve", "--port", "4200", "--host", "0.0.0.0", "--disable-host-check"]