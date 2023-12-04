#!/bin/bash
# entrypoint.sh

# Set the working directory in the container
cd /usr/src/app

# Apply database migrations
flask db upgrade

# Start the Flask application
exec flask run
