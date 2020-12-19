from __init__ import app
from flask import request, jsonify
from models import Constellation, Stars, ConstellationSchema, StarSchema


# App configuration
app.config['DEBUG'] = True

# Schema init
constellation_schema = ConstellationSchema()
constellations_schema = ConstellationSchema(many=True)

star_schema = StarSchema()
stars_schema = StarSchema(many=True)

# API logic

default = [{'AstroPy': 'no argument'}]


@app.route('/')
def home():
    return """<h1 style="text-align: center> 
                    This is AstroPy 
              </h1>"""


@app.route('/hello', methods=['GET'])
def greetings():
    if not request.args:
        return jsonify(default)

    response = {'name': request.args['name'], 'age': int(request.args['age'])}
    return jsonify(response)


@app.route('/astropy/api/v1/constellation', methods=['GET'])
def constellation():
    if not request.args:
        return jsonify(default)

    c = request.args['c']
    query_result = Constellation.query.filter_by(name=c).first_or_404()
    output = constellation_schema.dump(query_result)

    return jsonify(output)


@app.route('/astropy/api/v1/query', methods=['GET'])
def get_constellations_via_query():
    """ Parameters accepted: [quadrant as q, min_latitude as min, max_latitude as max] """

    if not request.args:
        return jsonify(default)

    if 'q' in request.args:
        obj_query = Constellation.query.filter_by(quadrant=request.args['q'])
        if 'min' in request.args and 'max' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'],
                                                      max_latitude=request.args['max'])
        if 'min' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'])
        if 'max' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      max_latitude=request.args['max'])

    if 'min' in request.args:
        obj_query = Constellation.query.filter_by(min_latitude=request.args['min'])
        if 'q' in request.args and 'max' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'],
                                                      max_latitude=request.args['max'])
        if 'q' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'])
        if 'max' in request.args:
            obj_query = Constellation.query.filter_by(min_latitude=request.args['min'],
                                                      max_latitude=request.args['max'])

    if 'max' in request.args:
        obj_query = Constellation.query.filter_by(max_latitude=request.args['max'])
        if 'min' in request.args and 'q' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      min_latitude=request.args['min'],
                                                      max_latitude=request.args['max'])
        if 'min' in request.args:
            obj_query = Constellation.query.filter_by(max_latitude=request.args['max'],
                                                      min_latitude=request.args['min'])
        if 'q' in request.args:
            obj_query = Constellation.query.filter_by(quadrant=request.args['q'],
                                                      max_latitude=request.args['max'])

    if obj_query is None or len(obj_query.all()) == 0:
        output = {'No record found': 404}
    else:
        output = constellations_schema.dump(obj_query)

    return jsonify(output)


@app.route('/astropy/api/v1/constellation/all')
def get_all_constellations():
    _all = Constellation.query.all()
    output = constellations_schema.dump(_all)
    return jsonify(output)


# TODO query path for stars


if __name__ == '__main__':
    app.run()
