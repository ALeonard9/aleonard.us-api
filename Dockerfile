# Use an official Python runtime as a parent image
FROM python:3.12-alpine3.19

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements/base.txt requirements/base.txt

# Install any needed packages specified in requirements.txt
RUN apk update && apk add --no-cache postgresql-dev gcc python3-dev musl-dev rust cargo && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt

# Copy the rest of the application
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "-m", "app.main", "--env", "dev"]
