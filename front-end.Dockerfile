FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV GOOGLE_APPLICATION_CREDENTIALS="AppData/credentials.json"
ENV GOOGLE_CLOUD_BUCKET=policyreader-pdfs

EXPOSE 3000

CMD npm run dev