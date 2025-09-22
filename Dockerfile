# Use official Python 3.13 slim image
FROM python:3.13-slim

# Install system dependencies needed for PyAudio
RUN apt-get update && apt-get install -y portaudio19-dev gcc && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port your app will run on (adjust if necessary)
EXPOSE 10000

# Run your FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
