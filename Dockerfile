# Use official slim Python 3.13 image
FROM python:3.13-slim

# Install system dependencies for PyAudio + build tools
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy all your project files into the container
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your app will run on (update if your app uses a different port)
EXPOSE 10000

# Command to start your FastAPI app (adjust if needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
