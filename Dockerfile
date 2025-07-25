FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Expose port 8080
EXPOSE 8080

# Set env var
ENV PORT=8080

# Use gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
