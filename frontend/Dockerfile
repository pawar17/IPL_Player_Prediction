# Use a Python base image
FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install the dependencies from the requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port the app will run on (port 8000 is the default for Gunicorn)
EXPOSE 8000

# Command to run the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
