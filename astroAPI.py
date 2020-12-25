from __init__ import app
from flask import request, jsonify
from models import Constellation, Stars, ConstellationSchema, SingleStarSchema, StarSchema
from messages import messages
from werkzeug import exceptions
import functions

# Schema init
constellation_schema = ConstellationSchema()
constellations_schema = ConstellationSchema(many=True)

single_star_schema = SingleStarSchema()
multiple_stars_schema = SingleStarSchema(many=True)


# API logic
@app.route('/')
def home():
    return jsonify({'Welcome': messages['welcome']})


@app.route('/hello', methods=['GET'])
def greetings():
    if not request.args:
        return jsonify({'message': messages['hello']})

    response = {'Hello, There': [request.args['name'],
                                 request.args['last']]}
    return jsonify(response)


@app.route('/astropy/api/v1/constellation', methods=['GET'])
def get_constellation():
    if not request.args:
        return jsonify({'message': messages['no argument']})

    try:
        c = request.args['c']
    except exceptions.BadRequestKeyError:
        return jsonify({'message': messages['bad request']})

    query_result = Constellation.query.filter_by(name=c).first_or_404()
    output = constellation_schema.dump(query_result)

    return jsonify({'constellation': output})


@app.route('/astropy/api/v1/query', methods=['GET'])
def get_constellations_via_query():
    """ Parameters accepted: [quadrant as q, min_latitude as min, max_latitude as max] """

    if not request.args:
        return jsonify({'message': messages['no argument']})

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
        output = {'message': messages['not found']}
    else:
        output = constellations_schema.dump(obj_query)

    return jsonify({'constellation': output})


@app.route('/astropy/api/v1/constellation/all')
def get_all_constellations():
    _all = Constellation.query.all()
    output = constellations_schema.dump(_all)
    return jsonify({'constellations': output})


@app.route('/astropy/api/v1/star')
def get_star():
    if not request.args:
        return jsonify({'message': messages['no argument']})

    s = request.args['s']
    query_result = Stars.query.filter_by(star=s).first_or_404()
    output = single_star_schema.dump(query_result)

    return jsonify({'star': output})


@app.route('/astropy/api/v1/star/all')
def get_all_stars():
    _all = Stars.query.all()
    output = multiple_stars_schema.dump(_all)

    return jsonify({'stars': output})


# TODO get stars via query -- distance only

@app.route('/astropy/api/v1/where-to-look')
def where_to_look():
    """ Parameters: [latitude as lat and longitude as lon, and the star to observe as s]
        Positive latitude indicates the Northern hemisphere, whereas negative
        the Southern hemisphere. Otherwise, if you don't have coordinates at hand
        the city is also an option, use city=... """

    # where to look (declination - position)
    # right ascension == number of hours behind the Sun on 21st March

    if not request.args:
        return jsonify({'message': messages['no argument']})

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
            return jsonify({'message': f"{city} not found"})
        response['lat'] = coordinates['lat']
        response['lon'] = coordinates['lon']
        lat = functions.check_if_north(coordinates['lat'])
        lon = functions.check_if_east(coordinates['lon'])
    else:
        return jsonify({'message': messages['no coordinates']})

    try:
        star = Stars.query.filter_by(star=s).first()
    except exceptions.NotFound:
        return jsonify({'message': messages['not found']})

    declination = star.declination
    RA = star.right_ascension
    response['declination'] = declination
    response['right ascension'] = RA
    int_declination = int(declination[:3])

    where = int_declination - lat

    if abs(where) > 90:
        response['where'] = f'{s} is not visible from your location'
        return response
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
    return jsonify(response)


@app.route('/astropy/api/v1/star/closest/<int:limit>')
def closest(limit):
    if limit <= 0:
        limit = 5
    elif limit > 25:
        limit = 25

    _closest = Stars.query.order_by('distance').limit(limit)
    output = multiple_stars_schema.dump(_closest)

    return jsonify(output)


@app.route('/astropy/api/v1/star/brightest/<int:limit>')
def brightest(limit):
    if limit <= 0:
        limit = 5
    elif limit > 25:
        limit = 25

    _brightest = Stars.query.order_by('app_magnitude').limit(limit)
    output = multiple_stars_schema.dump(_brightest)

    return jsonify(output)


if __name__ == '__main__':
    app.run()
