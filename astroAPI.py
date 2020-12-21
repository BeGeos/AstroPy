from __init__ import app
from flask import request, jsonify
from models import Constellation, Stars, ConstellationSchema, SingleStarSchema, StarSchema
from messages import messages
from werkzeug import exceptions

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

if __name__ == '__main__':
    app.run()
