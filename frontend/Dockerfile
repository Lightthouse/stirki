FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM busybox:stable
COPY --from=build /app/dist /app/dist
CMD ["sh", "-c", "rm -rf /dist/* && cp -r /app/dist/. /dist/"]
