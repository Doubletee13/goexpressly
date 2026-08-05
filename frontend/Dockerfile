# GoExpressly Frontend — Production Dockerfile
# nginx serves compiled public/ + dist/ assets

FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install --include=dev

COPY . .
RUN npm run build

# ── Production stage ──────────────────────────────────────────────
FROM nginx:alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/

# Copy static files
COPY --from=build /app/public /usr/share/nginx/html
COPY --from=build /app/dist   /usr/share/nginx/html/dist
COPY --from=build /app/src    /usr/share/nginx/html/src

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
