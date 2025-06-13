# Use Python 3.8 base image
FROM python:3.13

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["fastapi", "run",  "main.py" ,"--host", "0.0.0.0", "--port", "8000"]
