FROM node:22.13.0 AS builder
WORKDIR /app

COPY /package*.json .
RUN npm install

COPY . .
RUN npm run build

#Могут быть проблемы с версией nginx, дернуть, если другая понадобиться
FROM docker.io/nginx:alpine 
COPY ./build_config/default.conf /etc/nginx/conf.d/default.conf

WORKDIR /usr/share/nginx/html

RUN rm -rf *
COPY --from=builder /app/dist .

ENTRYPOINT ["nginx", "-g", "daemon off;"]