# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . ./
RUN npm run build

# Установка сервера для раздачи статических файлов
RUN npm install -g serve

# Команда для запуска сервера
CMD ["serve", "-s", "build"]
