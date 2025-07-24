# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

CMD ["python", "main.py"]

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
