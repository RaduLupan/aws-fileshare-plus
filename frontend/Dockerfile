# Use an official node image as a parent image
FROM node:24-slim AS builder

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the application files
COPY . .

# Build arguments from environment variables
ARG VITE_USER_POOL_ID
ARG VITE_USER_POOL_CLIENT_ID
ARG VITE_AWS_REGION
ARG VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL

# Set environment variables for the build
ENV VITE_USER_POOL_ID=${VITE_USER_POOL_ID}
ENV VITE_USER_POOL_CLIENT_ID=${VITE_USER_POOL_CLIENT_ID}
ENV VITE_AWS_REGION=${VITE_AWS_REGION}
ENV VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL=${VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL}

# Build the app for production
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy the build files to nginx's html directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config for SPA routing
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]