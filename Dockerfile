# Use official Playwright base image (includes Linux dependencies & Chromium)
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY cloud_bot.py .

# Expose port for Render Web Service health checks
EXPOSE 10000

# Start the bot
CMD ["python", "cloud_bot.py"]
