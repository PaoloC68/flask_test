# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install pipenv
RUN pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install Python dependencies
RUN pip install pipenv && pipenv install --system --deploy

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Make port 1337 available to the world outside this container
EXPOSE 1337

# Define environment variables for PostgreSQL connection
ENV PGHOST=postgres_host
ENV PGPORT=5432
ENV PGUSER=postgres
ENV PGPASSWORD=""
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=1337

# Copy entrypoint script into the container
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

# Set the entrypoint script to be executed
ENTRYPOINT ["./entrypoint.sh"]
