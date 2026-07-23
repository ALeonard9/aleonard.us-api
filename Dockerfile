# Use an official Python runtime as a parent image
FROM python:3.14.5-alpine

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN addgroup -S adam && adduser -S adam -G adam

# Set up PATH for pip installations
ENV PATH="/home/adam/.local/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY --chown=adam:adam requirements/base.txt requirements/base.txt

# Install system dependencies as root
USER root
RUN apk update && apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    rust \
    cargo \
    xz

# Switch to non-root user for pip operations
USER adam

# Install Python packages as non-root user
RUN pip install --no-cache-dir --upgrade "pip>=26.1.2" && \
    pip install --no-cache-dir -r requirements/base.txt

# Copy the rest of the application with correct ownership
COPY --chown=adam:adam . .

# Make port 8000 available
EXPOSE 8000

# Run app.py when the container launches
CMD ["sh", "-c", "python -m app.main"]
