# Use Python 3.12 base image
FROM python:3.12-bullseye

# Install system dependencies + Node.js 18
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs postgresql-client xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy backend and frontend code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY entrypoint.sh .

# Fix Windows line endings (CRLF -> LF)
RUN sed -i 's/\r//' /app/entrypoint.sh

# Build frontend (Vite outputs directly to backend/static)
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Set working directory to backend so fastapi_app package is found
WORKDIR /app/backend
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Start the app
CMD ["bash", "/app/entrypoint.sh"]