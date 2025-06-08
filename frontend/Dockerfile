# Use an official node image as a parent image
FROM node:24-slim

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the application files
COPY . .

# Build the app for production
RUN npm run build

# Use an official nginx image to serve the build
FROM nginx:alpine

# Copy the build files to nginx's html directory
COPY --from=0 /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]