FROM python:3.9-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Set working directory
WORKDIR /app

# Copy code
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# EXPOSE port (important for Railway)
EXPOSE 8080

# Start the Flask app
CMD ["python", "app.py"]
