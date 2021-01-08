from __init__ import app
from flask import request, jsonify
from models import db, Constellation, Stars, ConstellationSchema, SingleStarSchema, StarSchema
from models import User, AuthKeys, SecurityCodes, Recovery
from messages import messages
from werkzeug import exceptions
from flask_cors import CORS
import functions
from wrappers import auth_key_required
from datetime import datetime, timedelta

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


# Main routes to create a user and an authentication key to be used in API calls
@app.route('/astropy/api/v1/create-user', methods=['POST'])
def create_user():
    """To create a user send a post request with username, password and a valid email address"""

    username = request.get_json()['username']
    if not functions.is_username_available(username):
        return jsonify({'message': f'{username} already exists'}), 400
    password = request.get_json()['password']
    if not functions.is_password_valid(password):
        return jsonify({'message': "Invalid password, it must be at least 4 characters long "
                                   "and remember, it's for your own good"}), 400
    email = request.get_json()['email']
    # TODO API check for valid email address
    if not functions.is_email_available(email):
        return jsonify({'message': f'{email} already exists'}), 400
    new_user = User(username=username, password=password,
                    email=email, date_created=datetime.utcnow())
    db.session.add(new_user)
    db.session.commit()
    security_code = functions.code_generator()
    exp = datetime.utcnow() + timedelta(seconds=600)
    user_sc = SecurityCodes(user_id=new_user.id, code=security_code, expiration=int(exp.timestamp()))
    db.session.add(user_sc)
    db.session.commit()
    functions.email_security_code(username, email, security_code)  # Static Does not return anything

    return jsonify({'message': f'{new_user} was created successfully!',
                    'information': 'To request an api key make a post request to /create-auth-key'
                                   ', specify a username and a valid password. But before, '
                                   'make sure to verify your email address',
                    'next step': 'Check your email for the verification process',
                    'recovery': 'If you want to recover/change your password go to /astropy/api/v1/recovery'
                                '\nTo recover/change you email address go to /astropy/api/v1/recover-email\n'
                                'send post requests following the instructions provided in the documentation at '
                                '/astropy/api/documentation'}), 201


@app.route('/astropy/api/v1/create-auth-key', methods=['POST'])
def create_auth_key():
    """The post request must include the username and a valid password.
     It returns an api key to use for requests, as well as the expiration
     date in seconds since epoch"""

    user = request.get_json()['username']
    current_user = User.query.filter_by(username=user).first()
    if not current_user:
        return jsonify({'message': messages['invalid user']}), 401
    password = request.get_json()['password']
    if password != current_user.password:
        return jsonify({'message': messages['invalid password']}), 403
    if not current_user.confirmed:
        return jsonify({'message': 'User is not confirmed'}), 403
    uid = current_user.id

    key = functions.key_generator()
    exp = datetime.utcnow() + timedelta(seconds=3600)
    try:
        new_key = AuthKeys(user_id=uid, key=key, expiration_date=int(exp.timestamp()))
        db.session.add(new_key)
        db.session.commit()
    except exceptions:
        return jsonify({'message': 'Something went wrong'}), 500

    return jsonify({'id': new_key.id,
                    'user': str(new_key.user),
                    'api key': new_key.key,
                    'expiration date': new_key.expiration_date}), 201


# Verification route
@app.route('/astropy/api/v1/verification', methods=['POST'])
def verification():
    """Verification route for users. It takes a post request with the username
    and the security code available, sent via email"""
    username = request.get_json()['username']
    six_digit_code = request.get_json()['security code']

    # Verify it exists, it belongs to that username, it hasn't expired
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    # User has 5 attempts for the code -- security issues
    if user.attempts == 0:
        return jsonify({'message': 'No more attempts left, you must wait'}), 401
    user.attempts -= 1
    db.session.commit()
    if user.security_code is None:
        return jsonify({'message': 'Security code does not exist'}), 401
    if user.security_code.code != six_digit_code:
        return jsonify({'message': 'Invalid security code'}), 401

    record = SecurityCodes.query.filter_by(user_id=user.id).first()
    if record.expiration < datetime.utcnow().timestamp():
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Security code has expired'})

    user.confirmed = True
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': f'{username} has been confirmed'}), 202


# New 6-digit-code request
@app.route('/astropy/api/v1/new-code-request', methods=['POST'])
def new_code_request():
    """Backup for a new code in case the previous one was lost, expired or
    server didn't send it due to random errors"""
    username = request.get_json()['username']
    password = request.get_json()['password']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    if password != user.password:
        return jsonify({'message': 'Invalid password'}), 401
    security_code = functions.code_generator()
    exp = datetime.utcnow() + timedelta(seconds=600)

    if user.security_code is not None:
        record = SecurityCodes.query.filter_by(user_id=user.id).first()
        db.session.delete(record)
        db.session.commit()

    user_sc = SecurityCodes(user_id=user.id, code=security_code, expiration=int(exp.timestamp()))
    db.session.add(user_sc)
    db.session.commit()
    functions.email_security_code(username, user.email, security_code)
    return jsonify({'message': 'Code sent correctly, check your email'}), 202


# Password Recovery
@app.route('/astropy/api/v1/recovery', methods=['POST'])
def recovery_request():
    """In case user lost his/her password, or wants to change it.
    Send a post request via json to the URL with username and email address"""
    username = request.get_json()['username']
    _email = request.get_json()['email']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    if not user.confirmed:
        return jsonify({'message': 'User not confirmed'}), 401
    if user.email != _email:
        return jsonify({'message': 'Request not accepted'}), 400
    base_url = 'http://localhost:5000/astropy/api/v1/recovery/'
    extension = functions.ext_generator()
    expire_on = datetime.utcnow() + timedelta(days=1)
    recovery_link = Recovery(user_id=user.id, url_extension=extension,
                             exp_date=int(expire_on.timestamp()))
    db.session.add(recovery_link)
    db.session.commit()
    link = base_url + extension
    functions.email_recovery_password(username, _email, link)
    return jsonify({'message': 'Request accepted, check your email'}), 202


@app.route('/astropy/api/v1/recovery/<slug>', methods=['POST'])
def password_recovery(slug):
    recovery_code = Recovery.query.filter_by(url_extension=slug).first()
    if not recovery_code:
        return jsonify({'message': 'Invalid URL'}), 404
    if recovery_code.exp_date < datetime.utcnow().timestamp():
        return jsonify({'message': 'This link has expired'})

    username = request.get_json()['username']
    new_password = request.get_json()['new password']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid user'}), 401
    if recovery_code.user_id != user.id:
        return jsonify({'message': 'Invalid code'}), 401

    user.password = new_password
    db.session.delete(recovery_code)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully!'}), 202


@app.route('/astropy/api/v1/recover-email', methods=['POST'])
def email_recovery():
    """Send a post request with username, password and the new or correct email address"""
    username = request.get_json()['username']
    password = request.get_json()['password']
    _email = request.get_json()['new email']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    if user.password != password:
        return jsonify({'message': 'Invalid password'}), 401
    if not functions.is_email_available(_email):
        return jsonify({'message': f'{_email} already exists'}), 400
    if user.confirmed:
        user.confirmed = False
        db.session.commit()
    if user.security_code is not None:
        record = SecurityCodes.query.filter_by(user_id=user.id).first()
        db.session.delete(record)
        db.session.commit()
    user.email = _email
    db.session.commit()

    security_code = functions.code_generator()
    exp = datetime.utcnow() + timedelta(seconds=600)
    user_sc = SecurityCodes(user_id=user.id, code=security_code, expiration=int(exp.timestamp()))
    db.session.add(user_sc)
    db.session.commit()
    functions.email_security_code(username, _email, security_code)
    return jsonify({'message': 'Email was updated successfully! Check Your email for verification'}), 200


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
            return jsonify({'message': f"{city} not found"}), 204
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


if __name__ == '__main__':
    app.run()
