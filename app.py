import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, BIGINT
import uuid
from flask import request, jsonify
import math
from flask_migrate import Migrate

db = SQLAlchemy()


class City(db.Model):
    __tablename__ = 'cities'
    city_uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    geo_location_latitude = db.Column(db.Float, nullable=False)
    geo_location_longitude = db.Column(db.Float, nullable=False)
    beauty = db.Column(db.Enum('Ugly', 'Average', 'Gorgeous', name='beauty_enum'), nullable=False)
    population = db.Column(BIGINT, nullable=False)
    allied_cities = db.Column(db.ARRAY(UUID), default=[])

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:@localhost/gridscale'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
if os.environ.get('FLASK_ENV') == 'testing':
    app.config.from_object('app.TestConfig')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        f"postgresql://{os.environ.get('PGUSER', 'postgres')}:" \
        f"{os.environ.get('PGPASSWORD', '')}@" \
        f"{os.environ.get('PGHOST', 'localhost')}:" \
        f"{os.environ.get('PGPORT', '5432')}/gridscale"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route('/cities', methods=['POST'])
def create_city():
    data = request.json

    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    new_city = City(
        name=data['name'],
        geo_location_latitude=data['geo_location_latitude'],
        geo_location_longitude=data['geo_location_longitude'],
        beauty=data['beauty'],
        population=data['population'],
        allied_cities=data.get('allied_cities', [])
    )

    db.session.add(new_city)
    db.session.commit()

    return jsonify({'city_uuid': new_city.city_uuid}), 201


@app.route('/cities/<city_uuid>', methods=['PUT'])
def update_city(city_uuid):
    city = City.query.get(city_uuid)
    if not city:
        return jsonify({'error': 'City not found'}), 404

    data = request.json

    if 'allied_cities' in data:
        new_allies_uuids = set(map(uuid.UUID, data['allied_cities']))
        current_allies_uuids = set(city.allied_cities)

        # Update alliances for removed allies

        for ally_uuid in current_allies_uuids - new_allies_uuids:
            ally = City.query.get(ally_uuid)
            if ally:
                ally.allied_cities = [uuid for uuid in ally.allied_cities if uuid != city.city_uuid]

        # Update alliances for added allies
        for ally_uuid in new_allies_uuids - current_allies_uuids:
            ally = City.query.get(ally_uuid)
            if ally:
                updated_allies = ally.allied_cities + [city.city_uuid]
                ally.allied_cities = updated_allies

        # Update city's alliances
        city.allied_cities = list(new_allies_uuids)

    # Update other fields
    for field in ['name', 'geo_location_latitude', 'geo_location_longitude', 'beauty', 'population']:
        if field in data:
            setattr(city, field, data[field])

    db.session.commit()
    return jsonify({'message': 'City updated successfully'}), 200


@app.route('/cities/<city_uuid>', methods=['DELETE'])
def delete_city(city_uuid):
    city = City.query.get(city_uuid)

    if city is None:
        return jsonify({'error': 'City not found'}), 404

    # Remove the city as an ally from all former allies
    former_allies = City.query.filter(City.city_uuid.in_(city.allied_cities)).all()
    for ally in former_allies:
        if city.city_uuid in ally.allied_cities:
            ally.allied_cities.remove(city.city_uuid)

    # Delete the city
    db.session.delete(city)
    db.session.commit()

    return jsonify({'message': 'City deleted successfully'}), 200


@app.route('/cities', methods=['GET'])
@app.route('/cities/<city_uuid>', methods=['GET'])
def get_cities(city_uuid=None):
    if city_uuid:
        city = City.query.get(city_uuid)
        if city is None:
            return jsonify({'error': 'City not found'}), 404

        # Calculate allied_power here
        allied_power = calculate_allied_power(city)

        city_data = {**city.as_dict(), 'allied_power': allied_power}
        return jsonify(city_data), 200
    else:
        cities = City.query.all()
        return jsonify([city.as_dict() for city in cities]), 200


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_allied_power(city):
    allied_power = city.population

    for ally_uuid in city.allied_cities:
        ally = City.query.get(ally_uuid)
        if ally:
            distance = haversine(city.geo_location_latitude, city.geo_location_longitude,
                                 ally.geo_location_latitude, ally.geo_location_longitude)

            # Adjusting population based on distance
            if distance > 10000:  # more than 10000 km
                allied_power += round(ally.population / 4)
            elif distance > 1000:  # more than 1000 km and less than or equal to 10000 km
                allied_power += round(ally.population / 2)
            else:
                allied_power += ally.population

    return allied_power


# Initialize SQLAlchemy with the app, regardless of the environment
db.init_app(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
