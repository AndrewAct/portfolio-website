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

# Start the application using ng serve
# CMD ["npm", "start", "--", "--host", "0.0.0.0"]
CMD ng serve --port 4200 --host 0.0.0.0  --disable-host-check