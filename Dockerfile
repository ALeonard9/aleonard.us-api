# Use an official Python runtime as a parent image
FROM python:3.12-alpine3.19

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN addgroup -S app && adduser -S app -G app

# Copy requirements first to leverage Docker cache
COPY requirements/base.txt requirements/base.txt

# Install PostgreSQL client
USER root
RUN apk update && apk add --no-cache postgresql-dev gcc python3-dev musl-dev rust cargo

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt

# Copy the rest of the application
COPY . .

# Change ownership of /app to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "-m", "app.main", "--env", "dev"]
