# official Node.js image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json 
COPY ui/package.json ./

# Install dependencies using npm
RUN npm install --legacy-peer-deps

# Copy the rest of the application code
COPY . .

# Build the app 
RUN npm run build

# Set environment
ENV NODE_ENV=production
ENV PORT=3000

# Expose the port your app listens on
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]
