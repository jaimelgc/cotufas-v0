# Stage 1: build Angular
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
# Build with production config
RUN npm run build -- --configuration production

# Stage 2: serve with Nginx
FROM nginx:alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy built Angular dist
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Angular routing support (handle deep links)
COPY nginx.spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80