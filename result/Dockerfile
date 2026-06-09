FROM node:18-slim
WORKDIR /app

# Kopiowanie wyłącznie plików manifestu zależności
COPY package*.json .

# Instalacja zależności.
RUN npm ci && npm cache clean --force

# Kopiowanie pozostałego kodu źródłowego aplikacji.
COPY . .

ENV PORT=80
EXPOSE 80

CMD ["node", "server.js"]



