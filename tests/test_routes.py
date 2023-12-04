import json

import pytest
from app import app, db, City, haversine  # Import your Flask app, database, and models
import os

import uuid  # Make sure to import uuid

os.environ['FLASK_ENV'] = 'testing'
@pytest.fixture
def test_client():
    # Set up your Flask test environment
    app.config.from_object('app.TestConfig')  # Or however you configure your test environment

    # Create an application context for the tests to run in
    with app.app_context():
        # # Create the database and the database tables
        # db.create_all()

        # Your testing code will go here

        # This is the test client that your test will use to make requests
        # to your application
        testing_client = app.test_client()

        # Establish an application context before running the tests
        ctx = app.app_context()
        ctx.push()

        yield testing_client  # this is where the testing happens!

        ctx.pop()

        # # Tear down the database afterwards
        # db.drop_all()


def test_create_city(test_client):
    response = test_client.post('/cities', json={
        'name': 'Test City',
        'geo_location_latitude': 40.7128,
        'geo_location_longitude': -74.0060,
        'beauty': 'Average',
        'population': 1000000,
    })
    assert response.status_code == 201
    assert 'city_uuid' in response.json


@pytest.fixture
def create_city(test_client):
    # Use the 'client' fixture to ensure the application context is active
    with app.app_context():
        city = City(
            name="Test City",
            geo_location_latitude=40.7128,
            geo_location_longitude=-74.0060,
            beauty="Average",
            population=8000000
        )
        db.session.add(city)
        db.session.commit()
        return city.city_uuid  # Return the UUID instead of the city object



def test_update_city(test_client, create_city):
    city_uuid = create_city  # This is the UUID of the city
    url = f'/cities/{city_uuid}'
    updated_data = {
        'name': 'New City Name',
        'geo_location_latitude': 55.7558,
        'geo_location_longitude': 37.6173,
        'beauty': 'Gorgeous',
        'population': 10000000
    }
    response = test_client.put(url, data=json.dumps(updated_data), content_type='application/json')
    assert response.status_code == 200
    with app.app_context():
        updated_city = City.query.get(city_uuid)
        assert updated_city.name == updated_data['name']
        assert updated_city.population == updated_data['population']

def test_update_nonexistent_city(test_client):
    # Use a valid UUID format string that is not in your database
    nonexistent_uuid = '00000000-0000-0000-0000-000000000000'
    url = f'/cities/{nonexistent_uuid}'
    response = test_client.put(url, data=json.dumps({}), content_type='application/json')
    assert response.status_code == 404
@pytest.fixture
def create_cities():
    with app.app_context():
        city1 = City(
            name="Paris",
            geo_location_latitude=48.8566,  # Paris
            geo_location_longitude=2.3522,
            beauty="Average",
            population=100000,
            allied_cities=[]
        )
        city2 = City(
            name="Beijing",
            geo_location_latitude=39.9042,  # Beijing
            geo_location_longitude=116.4074,
            beauty="Gorgeous",
            population=200000,
            allied_cities=[]
        )
        city3 = City(
            name="Sydney",
            geo_location_latitude=-33.8688,  # Sydney
            geo_location_longitude=151.2093,
            beauty="Ugly",
            population=300000,
            allied_cities=[]
        )


        db.session.add_all([city1, city2, city3])
        db.session.commit()

        # Retrieve the UUIDs as strings from the created cities
        city1_uuid = str(city1.city_uuid)
        city2_uuid = str(city2.city_uuid)
        city3_uuid = str(city3.city_uuid)

        return city1_uuid, city2_uuid, city3_uuid


def test_update_alliances(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities
    # Print the UUIDs from the database
    with app.app_context():
        city1 = City.query.get(city1_uuid)
        city2 = City.query.get(city2_uuid)
        city3 = City.query.get(city3_uuid)
        print("City1 UUID in database:", city1.city_uuid)
        print("City2 UUID in database:", city2.city_uuid)
        print("City3 UUID in database:", city3.city_uuid)
    # Initially set City1 allied with City2 and City3
    with app.app_context():
        city1 = City.query.get(city1_uuid)
        print("Allied cities of City1:", city1.allied_cities)  # Debugging print
        city1.allied_cities = [city2_uuid, city3_uuid]
        db.session.commit()

    # Update City2 to be allied with City3
    response = test_client.put(f'/cities/{city2_uuid}', json={'allied_cities': [str(city3_uuid)]})
    print("Response JSON:", response.json)
    assert response.status_code == 200


    # Check the updated alliances
    with app.app_context():
        updated_city1 = City.query.get(city1_uuid)
        updated_city2 = City.query.get(city2_uuid)
        updated_city3 = City.query.get(city3_uuid)
        print("Updated alliances of city1:", updated_city1.allied_cities)  # Debugging print
        print("Updated alliances of city2:", updated_city2.allied_cities)  # Debugging print
        print("Updated alliances of city3:", updated_city3.allied_cities)  # Debugging print
        db.session.commit()
        print("city3_uuid:", city3_uuid)
        print("updated_city1.allied_cities:", updated_city1.allied_cities)
        # Assertions based on the corrected UUIDs
        assert uuid.UUID(city3_uuid) in updated_city1.allied_cities
        assert uuid.UUID(city3_uuid) in updated_city1.allied_cities
        assert uuid.UUID(city3_uuid) in updated_city2.allied_cities
        assert uuid.UUID(city2_uuid) in updated_city3.allied_cities

def test_remove_all_alliances(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities
    # Initial setup: City1 allied with City2 and City3
    with app.app_context():
        city1 = City.query.get(city1_uuid)
        city1.allied_cities = [city2_uuid, city3_uuid]
        db.session.commit()

    # City1 removes all alliances
    response = test_client.put(f'/cities/{city1_uuid}', json={'allied_cities': []})
    assert response.status_code == 200

    # Check updated alliances
    with app.app_context():
        updated_city1 = City.query.get(city1_uuid)
        updated_city2 = City.query.get(city2_uuid)
        updated_city3 = City.query.get(city3_uuid)
        assert updated_city1.allied_cities == []
        assert city1_uuid not in updated_city2.allied_cities
        assert city1_uuid not in updated_city3.allied_cities

def test_add_new_alliances(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities
    # City1 forms new alliances with City2 and City3
    response = test_client.put(f'/cities/{city1_uuid}', json={'allied_cities': [city2_uuid, city3_uuid]})
    assert response.status_code == 200

    # Check updated alliances
    with app.app_context():
        updated_city1 = City.query.get(city1_uuid)
        updated_city2 = City.query.get(city2_uuid)
        updated_city3 = City.query.get(city3_uuid)
        assert uuid.UUID(city2_uuid) in updated_city1.allied_cities
        assert uuid.UUID(city3_uuid) in updated_city1.allied_cities
        assert uuid.UUID(city1_uuid) in updated_city2.allied_cities
        assert uuid.UUID(city1_uuid) in updated_city3.allied_cities

def test_update_with_same_allies(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities
    # City1 initially allied with City2
    with app.app_context():
        city1 = City.query.get(city1_uuid)
        city1.allied_cities = [city2_uuid, city3_uuid]
        city2 = City.query.get(city2_uuid)
        city2.allied_cities = [city1_uuid]
        city3 = City.query.get(city3_uuid)
        city3.allied_cities = [city1_uuid]
        db.session.commit()

    # City1 updates with the same ally
    response = test_client.put(f'/cities/{city1_uuid}', json={'allied_cities': [city2_uuid, city3_uuid]})
    assert response.status_code == 200

    # Check that there's no change in alliances
    with app.app_context():
        updated_city1 = City.query.get(city1_uuid)
        updated_city2 = City.query.get(city2_uuid)
        assert uuid.UUID(city2_uuid) in updated_city1.allied_cities
        assert uuid.UUID(city1_uuid) in updated_city2.allied_cities

def test_complex_alliance_changes(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities
    # Initial setup: City1 allied with City2
    with app.app_context():
        city1 = City.query.get(city1_uuid)
        city1.allied_cities = [city2_uuid]
        db.session.commit()

    # City1 changes alliances to only include City3
    response = test_client.put(f'/cities/{city1_uuid}', json={'allied_cities': [city3_uuid]})
    assert response.status_code == 200

    # Check updated alliances
    with app.app_context():
        updated_city1 = City.query.get(city1_uuid)
        updated_city2 = City.query.get(city2_uuid)
        updated_city3 = City.query.get(city3_uuid)
        assert uuid.UUID(city3_uuid) in updated_city1.allied_cities
        assert city1_uuid not in updated_city2.allied_cities
        assert uuid.UUID(city1_uuid) in updated_city3.allied_cities


def test_allied_power_calculation(test_client, create_cities):
    city1_uuid, city2_uuid, city3_uuid = create_cities

    with app.app_context():
        # Load cities within the session context
        city1 = City.query.get(city1_uuid)
        city2 = City.query.get(city2_uuid)
        city3 = City.query.get(city3_uuid)

        # Form alliances
        city1.allied_cities = [city2_uuid, city3_uuid]
        db.session.commit()

        # Calculate expected allied power for City1 within the session
        expected_allied_power = city1.population
        for ally_uuid in city1.allied_cities:
            ally = City.query.get(ally_uuid)
            distance = haversine(city1.geo_location_latitude, city1.geo_location_longitude,
                                 ally.geo_location_latitude, ally.geo_location_longitude)

            if distance > 10000:
                expected_allied_power += round(ally.population / 4)
            elif distance > 1000:
                expected_allied_power += round(ally.population / 2)
            else:
                expected_allied_power += ally.population

    # Retrieve the calculated allied power using the API
    response = test_client.get(f'/cities/{city1_uuid}')
    assert response.status_code == 200
    calculated_allied_power = response.json['allied_power']

    # Compare the expected and calculated allied power
    assert expected_allied_power == calculated_allied_power

