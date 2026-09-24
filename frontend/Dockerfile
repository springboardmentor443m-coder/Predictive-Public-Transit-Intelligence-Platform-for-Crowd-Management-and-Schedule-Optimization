# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy all frontend files
COPY package*.json ./
COPY package-lock.json ./
COPY index.html ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY public/ ./public/
COPY src/ ./src/

# Install dependencies
RUN npm install

# Build the frontend
RUN npm run build

# Expose port
EXPOSE 5173

# Run the frontend dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
