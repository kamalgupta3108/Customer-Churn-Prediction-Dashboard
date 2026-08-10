# frontend/Dockerfile
# ----------------------
# React apps need a two-phase approach in Docker, called a "multi-stage
# build": Phase 1 (build) turns our .jsx source code into plain static
# HTML/CSS/JS files (via `npm run build`, same as we've been doing).
# Phase 2 (serve) takes ONLY those final static files and serves them with
# a lightweight web server - we don't need Node.js or any of our
# node_modules in the final container at all, just the finished output.
# This keeps the final image much smaller than if we shipped the whole
# Node.js toolchain along with it.

# ---- Phase 1: build ----
FROM node:20-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# ARG values are only available during the build, not at container
# runtime - which is exactly what we need, since Vite reads env variables
# and "bakes" them into the static JS files at build time (`npm run
# build`), not when the final nginx container later starts up.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build
# After this line, /app/dist contains plain HTML/CSS/JS - the exact same
# output folder `npm run build` has been creating locally all along.

# ---- Phase 2: serve ----
# nginx is a lightweight, battle-tested web server - perfect for serving
# a folder of static files efficiently.
FROM nginx:alpine

# Copy ONLY the built static files from Phase 1 into nginx's default
# folder for serving web content. Notice we reference "--from=build" -
# this reaches back into the previous phase's filesystem, even though
# that phase's container itself gets discarded.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
