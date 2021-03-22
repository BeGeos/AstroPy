from . import app, db
from flask import request, jsonify
from .models import Constellation, Stars, ConstellationSchema, SingleStarSchema
from .models import AuthKeys
from .messages import messages
from werkzeug import exceptions
from flask_cors import CORS
from .functions import *
from .wrappers import auth_key_required, admin_only
from .env import secret_keys

# Schema init
constellation_schema = ConstellationSchema()
constellations_schema = ConstellationSchema(many=True)

single_star_schema = SingleStarSchema()
multiple_stars_schema = SingleStarSchema(many=True)

# CORS handling
CORS(app)


# API logic
@app.route('/astropy')
def home():
    return jsonify({'Welcome': messages['welcome']})


@app.route('/astropy/hello', methods=['GET'])
def greetings():
    """Greeting message to the user, insert first and last name in the query
    URL and you will receive a small greeting message"""
    if not request.args:
        return jsonify({'message': messages['hello']}), 204

    try:
        name_last = [request.args['name'], request.args['last']]

        name = " ".join(name_last)

        response = {'Hello, There': name}
        return jsonify(response), 200
    except exceptions.BadRequestKeyError as b:
        return jsonify({'message': 'Bad Request'}), 400


# Main API routes for constellations, stars and TODO planets
@app.route('/astropy/api/v1/constellation', methods=['GET', 'POST'])
@auth_key_required
def get_constellation():
    """Main path to make get requests for constellations.
    It takes the c parameter only."""
    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    try:
        c = request.args['c'].lower()
    except exceptions.BadRequestKeyError:
        return jsonify({'message': messages['bad request']}), 400

    query_result = Constellation.query.filter_by(name=c).first_or_404()
    output = constellation_schema.dump(query_result)

    return jsonify({'constellation': output}), 200


@app.route('/astropy/api/v1/query', methods=['GET', 'POST'])
@auth_key_required
def get_constellations_via_query():
    """It allows flexibility upon constellation lookups. As a simple db search.
    Parameters accepted: [quadrant as q, min latitude as min, max latitude as max]"""

    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    obj_query = None

    if 'q' in request.args and 'min' in request.args and 'max' in request.args:
        obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'],
                                                           Constellation.min_latitude >= int(request.args['min']),
                                                           Constellation.max_latitude <= int(request.args['max']))

    if 'q' in request.args:
        obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'])

        if 'min' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'],
                                                               Constellation.min_latitude >= int(request.args['min']))

        if 'max' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'],
                                                               Constellation.max_latitude <= int(request.args['max']))

    if 'min' in request.args:
        obj_query = db.session.query(Constellation).filter(Constellation.min_latitude >= int(request.args['min']))

        if 'q' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'],
                                                               Constellation.min_latitude >= int(request.args['min']))
        if 'max' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.max_latitude <= int(request.args['max']),
                                                               Constellation.min_latitude >= int(request.args['min']))

    if 'max' in request.args:
        obj_query = db.session.query(Constellation).filter(Constellation.max_latitude >= int(request.args['max']))

        if 'min' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.max_latitude <= int(request.args['max']),
                                                               Constellation.min_latitude >= int(request.args['min']))
        if 'q' in request.args:
            obj_query = db.session.query(Constellation).filter(Constellation.quadrant == request.args['q'],
                                                               Constellation.max_latitude <= int(request.args['max']))

    if obj_query is None or len(obj_query.all()) == 0:
        return jsonify({'message': messages['not found']}), 404
    else:
        output = constellations_schema.dump(obj_query)

    return jsonify({'constellations': output}), 200


@app.route('/astropy/api/v1/constellation/all', methods=['POST'])
@admin_only
# @auth_key_required
def get_all_constellations():
    """Route that yields all the constellations: FYI there are 88"""
    _all = Constellation.query.all()
    output = constellations_schema.dump(_all)
    return jsonify({'constellations': output}), 200


@app.route('/astropy/api/v1/star', methods=['GET', 'POST'])
@auth_key_required
def get_star():
    """Route to get single stars from the query, only parameter as s accepted"""
    if not request.args:
        return jsonify({'message': messages['no argument']}), 400

    try:
        s = request.args['s'].lower()
        query_result = Stars.query.filter_by(star=s).first_or_404()
        output = single_star_schema.dump(query_result)
        return jsonify({'star': output}), 200

    except exceptions.BadRequestKeyError:
        return jsonify({'message': 'Bad Request'}), 400


@app.route('/astropy/api/v1/star/all')
@admin_only
# @auth_key_required
def get_all_stars():
    """It returns all the stars of all the constellations. They are in the range
    between 450-650, the real count would be way higher, but it considers
    the main and most visible stars of the constellation"""
    _all = Stars.query.all()
    output = multiple_stars_schema.dump(_all)

    return jsonify({'stars': output}), 200


# TODO get stars via query -- distance only

@app.route('/astropy/api/v1/where-to-look', methods=['GET', 'POST'])
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
    try:
        s = request.args['s'].lower()
    except exceptions.BadRequestKeyError:
        return jsonify({'message': 'No star specified'}), 400

    response['star'] = s
    star = Stars.query.filter_by(star=s).first()
    if not star:
        return jsonify({'message': messages['not found']}), 404
    if 'lat' in request.args and 'lon' in request.args:
        response['lat'] = request.args['lat']
        response['lon'] = request.args['lon']
        try:
            lat = int(request.args['lat'])
            lon = int(request.args['lon'])
        except ValueError:
            return jsonify({'message': 'Format not valid'}), 400
    elif 'city' in request.args:
        city = request.args['city']
        coordinates = geocoding_api(city)
        if coordinates is None:
            return jsonify({'message': f'{city} not found'}), 404
        response['lat'] = coordinates['lat']
        response['lon'] = coordinates['lon']
        lat = check_if_north(coordinates['lat'])
        lon = check_if_east(coordinates['lon'])
    else:
        return jsonify({'message': messages['no coordinates']}), 400

    declination = star.declination
    RA = star.right_ascension
    response['declination'] = declination
    int_declination = int(declination[:3])

    where = int_declination - lat

    if abs(where) > 90:
        response['where'] = f'{s} is not visible from your location'
        return jsonify(response), 200
    elif - 2 < where < + 2:
        response['where'] = 'just look over your head'
    elif where < 0:
        response['where'] = f'{abs(where)}° towards south'
    elif where > 0:
        response['where'] = f'{where}° towards north'

    # Get the time of sunrise and sunset from API call
    sun_time = sun_time_from_api(lat, lon)
    response['sunrise at location'] = sun_time['sunrise']
    response['sunset at location'] = sun_time['sunset']

    star_params = star_rising_time(int(RA[:2]), sun_time, RA)
    response['current delay'] = star_params['current ra']
    if star_params['message'] is not None:
        response['message'] = star_params['message']

    # Check for circumpolar stars
    if lat + int_declination > 90 or lat + int_declination < - 90:
        response['it rises'] = f'{s} is circumpolar star, hence it is always visible from this location'

    else:

        if 'star rise' in star_params:
            degrees = calculate_position(star_params['star rise'], sun_time['utc'])
            response['current position'] = degrees
            response['it rises'] = star_params['star rise']
            response['it sets'] = star_params['star set']
            # response['closest RA'] = star_time['closest delay']
        else:
            response['current position'] = star_params
    return jsonify(response), 200


@app.route('/astropy/api/v1/star/closest/<int:limit>', methods=['GET', 'POST'])
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


@app.route('/astropy/api/v1/star/brightest/<int:limit>', methods=['GET', 'POST'])
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
        return jsonify({'message': 'Invalid admin key'}), 403

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
        return jsonify({'message': 'Invalid admin key'}), 403
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
        return jsonify({'message': 'Invalid admin key'}), 403

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


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
