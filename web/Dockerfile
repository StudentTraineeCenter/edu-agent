# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_AZURE_ENTRA_TENANT_ID
ARG VITE_AZURE_ENTRA_CLIENT_ID
ARG VITE_SERVER_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

ENV VITE_AZURE_ENTRA_TENANT_ID=$VITE_AZURE_ENTRA_TENANT_ID \
    VITE_SERVER_URL=$VITE_SERVER_URL \
    VITE_AZURE_ENTRA_CLIENT_ID=$VITE_AZURE_ENTRA_CLIENT_ID \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Enable pnpm via Corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy manifest files first for better caching
COPY package.json pnpm-lock.yaml ./

# Pre-fetch dependencies to a content-addressable store
RUN pnpm fetch

# Copy source code and install deps from the store (offline)
COPY . .
RUN CI=true pnpm install --offline --frozen-lockfile

# Build the Vite SPA (static output in /dist)
RUN pnpm build

# ---- Runtime stage ----
FROM nginx:alpine

# Copy SPA-friendly nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]