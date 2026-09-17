# ==============================================================================
# STAGE 1: Build React Production Bundle
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Layer Caching: Install npm dependencies first
COPY package.json package-lock.json* ./
RUN npm install

# Copy frontend source code and compile
COPY . .
RUN npm run build

# ==============================================================================
# STAGE 2: Lightweight Production Nginx Web Server
# ==============================================================================
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA routing rules
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
