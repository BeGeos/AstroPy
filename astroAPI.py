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
    return """<h1 style="text-align: center; justify-content: center"> 
                    This is AstroPy 
              </h1>"""


@app.route('/hello', methods=['GET'])
def greetings():
    if not request.args:
        return jsonify(default)

    response = {'name': request.args['name'], 'age': int(request.args['age'])}
    return jsonify(response)


@app.route('/astropy/api/v1/constellations', methods=['GET'])
def constellation():
    if not request.args:
        return jsonify(default)

    c = request.args['c']
    query_result = Constellation.query.filter_by(name=c).first_or_404()
    output = constellation_schema.dump(query_result)

    return jsonify(output)


if __name__ == '__main__':
    app.run()
