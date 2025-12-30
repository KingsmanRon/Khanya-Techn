# MTP Frontend - Dockerfile
# Node.js 18 with React

# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Build for production
RUN yarn build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install serve for static file serving
RUN yarn global add serve

# Copy built assets from builder
COPY --from=builder /app/build ./build

# Create non-root user
RUN adduser -D appuser
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the application
CMD ["serve", "-s", "build", "-l", "3000"]

# Development stage
FROM node:18-alpine AS development

WORKDIR /app

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies
RUN yarn install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["yarn", "start"]
