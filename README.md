# City Management API

## Overview
This repository contains the Python source code for a RESTful API developed as part of the selection process for [Company Name]. The API is designed to manage city data, providing CRUD functionality. It is built using Flask and is containerized using Docker.

## Features
- **CRUD Operations:** Create, Read, Update, and Delete functionalities for city data.
- **Allied Cities Management:** Manage and calculate allied power based on city alliances and geographical distances.
- **Error Handling:** Robust error handling for malformed requests and invalid values.
- **Dockerized Application:** Easy deployment and consistent environment setup using Docker.

## Installation and Setup
1. Clone the repository.
2. Ensure Docker is installed on your system.
3. Run `docker build -t city-api .` to build the Docker image.
4. Run `docker run -p 1337:1337 city-api` to start the application.

## API Endpoints
- `POST /cities`: Create a new city.
- `GET /cities`: Retrieve all cities.
- `GET /cities/<city_uuid>`: Retrieve a single city by UUID.
- `PUT /cities/<city_uuid>`: Update a city's data.
- `DELETE /cities/<city_uuid>`: Delete a city.

## Database Schema
The SQL schema for initializing the PostgreSQL instance is managed using Flask-Migrate. This allows for effective handling of database migrations and schema changes.

## Contributing
Feel free to fork this repository and submit pull requests for any improvements or fixes.
