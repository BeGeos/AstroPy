from __init__ import app
from flask import request, jsonify
from models import db, Constellation, Stars, ConstellationSchema, SingleStarSchema, StarSchema
from models import AuthKeys
from messages import messages
from werkzeug import exceptions
from flask_cors import CORS
import functions
from wrappers import auth_key_required
from env import secret_keys

# Schema init
constellation_schema = ConstellationSchema()
constellations_schema = ConstellationSchema(many=True)

single_star_schema = SingleStarSchema()
multiple_stars_schema = SingleStarSchema(many=True)

# CORS handling
CORS(app)


# API logic
@app.route('/')
def home():
    return jsonify({'Welcome': messages['welcome']})


@app.route('/hello', methods=['GET'])
def greetings():
    """Greeting message to the user, insert first and last name in the query
    URL and you will receive a small greeting message"""
    if not request.args:
        return jsonify({'message': messages['hello']}), 204

    response = {'Hello, There': [request.args['name'],
                                 request.args['last']]}
    return jsonify(response), 200


# Main API routes for constellations, stars and TODO planets
@app.route('/astropy/api/v1/constellation', methods=['GET'])
@auth_key_required
def get_constellation():
    """Main path to make get requests for constellations.
    It takes the c parameter only."""
    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    try:
        c = request.args['c']
    except exceptions.BadRequestKeyError:
        return jsonify({'message': messages['bad request']}), 400

    query_result = Constellation.query.filter_by(name=c).first_or_404()
    output = constellation_schema.dump(query_result)

    return jsonify({'constellation': output}), 200


@app.route('/astropy/api/v1/query', methods=['GET'])
@auth_key_required
def get_constellations_via_query():
    """It allows flexibility upon constellation lookups. As a simple db search.
    Parameters accepted: [quadrant as q, min latitude as min, max latitude as max]"""

    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    if 'q' in request.args and 'min' in request.args and 'max' in request.args:
        obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                  min_latitude=request.args['min'],
                                                  max_latitude=request.args['max'])

    if 'q' in request.args:
        obj_query = Constellation.query.filter_by(quadrant=request.args['q'])

        if 'min' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'])
        if 'max' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      max_latitude=request.args['max'])

    if 'min' in request.args:
        obj_query = Constellation.query.filter_by(min_latitude=request.args['min'])

        if 'q' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'])
        if 'max' in request.args:
            obj_query = Constellation.query.filter_by(min_latitude=request.args['min'],
                                                      max_latitude=request.args['max'])

    if 'max' in request.args:
        obj_query = Constellation.query.filter_by(max_latitude=request.args['max'])

        if 'min' in request.args:
            obj_query = Constellation.query.filter_by(max_latitude=request.args['max'],
                                                      min_latitude=request.args['min'])
        if 'q' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      max_latitude=request.args['max'])

    if obj_query is None or len(obj_query.all()) == 0:
        return jsonify({'message': messages['not found']}), 204
    else:
        output = constellations_schema.dump(obj_query)

    return jsonify({'constellation': output}), 200


@app.route('/astropy/api/v1/constellation/all')
@auth_key_required
def get_all_constellations():
    """Route that yields all the constellations: FYI there are 88"""
    _all = Constellation.query.all()
    output = constellations_schema.dump(_all)
    return jsonify({'constellations': output}), 200


@app.route('/astropy/api/v1/star')
@auth_key_required
def get_star():
    """Route to get single stars from the query, only parameter as s accepted"""
    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    s = request.args['s']
    query_result = Stars.query.filter_by(star=s).first_or_404()
    output = single_star_schema.dump(query_result)

    return jsonify({'star': output}), 200


@app.route('/astropy/api/v1/star/all')
@auth_key_required
def get_all_stars():
    """It returns all the stars of all the constellations. They are in the range
    between 450-650, the real count would be way higher, but it considers
    the main and most visible stars of the constellation"""
    _all = Stars.query.all()
    output = multiple_stars_schema.dump(_all)

    return jsonify({'stars': output}), 200


# TODO get stars via query -- distance only

@app.route('/astropy/api/v1/where-to-look')
@auth_key_required
def where_to_look():
    """ Parameters: [latitude as lat and longitude as lon, and the star to observe as s]
        Positive latitude indicates the Northern hemisphere, whereas negative points to
        the Southern hemisphere. Otherwise, if you don't have coordinates at hand
        the city is also an option, use city=... """

    # where to look (declination - position)
    # right ascension == number of hours behind the Sun on 21st March

    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    response = {}
    s = request.args['s']
    response['star'] = s
    if 'lat' in request.args and 'lon' in request.args:
        response['lat'] = request.args['lat']
        response['lon'] = request.args['lon']
        lat = int(request.args['lat'])
        lon = int(request.args['lon'])
    elif 'city' in request.args:
        city = request.args['city']
        coordinates = functions.geocoding_api(city)
        if coordinates is None:
            return jsonify({'message': f'{city} not found'}), 204
        response['lat'] = coordinates['lat']
        response['lon'] = coordinates['lon']
        lat = functions.check_if_north(coordinates['lat'])
        lon = functions.check_if_east(coordinates['lon'])
    else:
        return jsonify({'message': messages['no coordinates']}), 400

    try:
        star = Stars.query.filter_by(star=s).first()
    except exceptions.NotFound:
        return jsonify({'message': messages['not found']}), 204

    declination = star.declination
    RA = star.right_ascension
    response['declination'] = declination
    response['right ascension'] = RA
    int_declination = int(declination[:3])

    where = int_declination - lat

    if abs(where) > 90:
        response['where'] = f'{s} is not visible from your location'
        return jsonify(response), 200
    elif - 2 < where < + 2:
        response['where'] = 'just look over your head'
    elif where < 0:
        response['where'] = f'{where}° towards south'
    elif where > 0:
        response['where'] = f'{where}° towards north'

    # Get the time of sunrise and sunset from API call
    sun_time = functions.sun_time_from_api(lat, lon)
    response['sunrise at location'] = sun_time['sunrise']
    response['sunset at location'] = sun_time['sunset']

    # Check for circumpolar stars
    if lat + int_declination > 90 or lat + int_declination < - 90:
        response['it rises'] = f'{s} is always visible from this location'

    else:
        star_time = functions.star_rising_time(int(RA[:2]), sun_time)
        if 'star rise' in star_time:
            degrees = functions.calculate_position(star_time['star rise'], sun_time['utc'])
            response['current position'] = degrees
            response['it rises'] = star_time['star rise']
            response['it sets'] = star_time['star set']
            # response['closest RA'] = star_time['closest delay']
        else:
            response['current position'] = star_time
    return jsonify(response), 200


@app.route('/astropy/api/v1/star/closest/<int:limit>')
@auth_key_required
def closest(limit):
    """Simple route to get the closest stars in the system, the integer is part
    of the route and it indicates the limit of results the search will yield.
    By default it is set to a max of 25 results, and a min of 5"""
    if limit <= 0:
        limit = 5
    elif limit > 25:
        limit = 25

    _closest = Stars.query.order_by('distance').limit(limit)
    output = multiple_stars_schema.dump(_closest)

    return jsonify(output), 200


@app.route('/astropy/api/v1/star/brightest/<int:limit>')
@auth_key_required
def brightest(limit):
    """Simple route to get the brightest stars in the system, the integer is part
    of the route and it indicates the limit of results the search will yield.
    By default it is set to a max of 25 results, and a min of 5"""
    if limit <= 0:
        limit = 5
    elif limit > 25:
        limit = 25

    _brightest = Stars.query.order_by('app_magnitude').limit(limit)
    output = multiple_stars_schema.dump(_brightest)

    return jsonify(output), 200


# Admin-only route
@app.route('/astropy/api/put-auth-key', methods=['PUT'])
def put_auth_in_db():
    admin_key = request.form['admin key']
    if admin_key != secret_keys['ADMIN_KEY']:
        return jsonify({'message': 'Wrong key provided'}), 401

    user_id = request.form['user id']
    api_key = request.form['api key']
    exp = request.form['exp date']
    new_auth_key = AuthKeys(user_id=user_id, key=api_key, expiration_date=exp)
    db.session.add(new_auth_key)
    db.session.commit()
    return jsonify({'message': 'Added correctly'}), 202


@app.route('/astropy/api/delete-auth-key', methods=['DELETE'])
def delete_auth_key():
    admin_key = request.form['admin key']
    if admin_key != secret_keys['ADMIN_KEY']:
        return jsonify({'message': 'Wrong key provided'}), 401
    user_id = request.form['user id']
    api_key = request.form['api key']
    record = AuthKeys.query.filter_by(user_id=user_id, key=api_key).first()
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Deleted correctly'}), 202
    except exceptions:
        return jsonify({'message': 'No record found'}), 404


@app.route('/astropy/api/update-auth-status', methods=['PUT'])
def update_auth_status():
    admin_key = request.form['admin key']
    if admin_key != secret_keys['ADMIN_KEY']:
        return jsonify({'message': 'Wrong key provided'}), 401

    user_id = request.form['user id']
    api_key = request.form['api key']
    status = request.form['status']
    auth_key = AuthKeys.query.filter_by(user_id=user_id, key=api_key).first()
    if status == 'True':
        auth_key.active = True
    elif status == 'False':
        auth_key.active = False
    db.session.commit()

    return jsonify({'message': 'Status updated'}), 200


if __name__ == '__main__':
    app.run()
