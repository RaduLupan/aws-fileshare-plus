# Use the latest slim variant of Python 3
FROM python:3-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements.txt for any dependencies
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add this line to unbuffer Python output
ENV PYTHONUNBUFFERED=1

# Copy the rest of your application code
COPY . .

# Expose the port the app runs on (optional but good for documentation)
EXPOSE 5000

# Run the command to start your Flask application. 
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]