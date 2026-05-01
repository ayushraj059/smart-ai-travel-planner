FROM node:20-slim AS builder

WORKDIR /app

ARG VITE_AUTH_URL=http://localhost:8001
ARG VITE_RAG_URL=http://localhost:8002
ARG VITE_USER_DETAILS_URL=http://localhost:8003
ARG VITE_DATABASE_URL=http://localhost:8000

ENV VITE_AUTH_URL=$VITE_AUTH_URL
ENV VITE_RAG_URL=$VITE_RAG_URL
ENV VITE_USER_DETAILS_URL=$VITE_USER_DETAILS_URL
ENV VITE_DATABASE_URL=$VITE_DATABASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
