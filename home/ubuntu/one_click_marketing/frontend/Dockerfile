# Stage 1: Build the Next.js application
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package.json and pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Build the Next.js application
RUN pnpm build

# Stage 2: Production image
FROM node:20-alpine

WORKDIR /app

# Set environment variables
ENV NODE_ENV production
# Google Cloud Run will set the PORT environment variable, Next.js will automatically use it.
# ENV PORT 8080 (Cloud Run sets this, so not strictly necessary to set it here but good for clarity)

# Copy built assets from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Expose the port the app runs on
# Next.js default is 3000, but Cloud Run expects PORT (default 8080)
# The start script should handle the PORT environment variable.
EXPOSE 8080

# Start the Next.js application
# The `next start` command will respect the PORT environment variable set by Cloud Run.
CMD ["pnpm", "start"]
