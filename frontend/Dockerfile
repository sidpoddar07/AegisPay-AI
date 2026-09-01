# =============================================================================
# AegisPay-AI — Frontend Multi-Stage Dockerfile
# Stage 1 (builder): Node 20 Alpine — compile TypeScript & bundle with Vite
# Stage 2 (serve):   Nginx Alpine   — ultra-fast static file serving
# =============================================================================

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer-cached unless package.json changes)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile --prefer-offline

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Remove default Nginx config and static content
RUN rm -rf /usr/share/nginx/html/* && rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the Vite build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx runs as its own non-privileged user by default on Alpine
EXPOSE 80

# Health check — Nginx should serve a 200 on the root
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
