# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app
ENV PYTHONPATH /app/src

# Copy the requirements file
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5004

# Set environment variables (if needed)
# ENV FLASK_APP=your_app.py

# Define the command to start the application
# CMD ["python", "your_app.py"]  # Or "gunicorn --bind 0.0.0.0:5000 your_app:app" for production
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5004"]