from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False


blank = [{'AstroPy': 'no argument'}]

ursa_major = {
        'name': 'Ursa Major',
        'right ascension': '10.67h',
        'declination': '+55.38°',
        'quadrant': 'NQ2',
        'min latitude': '-30°',
        'max latitude': '+90°',
        'main stars': [
            'Dubhe',
            'Merak',
            'Phecda',
            'Megrez',
            'Alioth',
            'Mizar',
            'Alkaid'
        ],
        'calculus': 21
}


@app.route('/')
def home():
    return '<h1>Hello, World</h1>'


@app.route('/hello', methods=['GET'])
def cheer():
    if not request.args:
        return jsonify(blank)

    response = {'name': request.args['name'], 'age': int(request.args['age'])}
    return jsonify(response)


@app.route('/astropy/api/v1/constellations', methods=['GET'])
def constellation():
    if not request.args:
        return jsonify(blank)

    c = request.args['c']
    try:
        result = int(request.args['add']) + ursa_major['calculus']
        ursa_major['calculus'] = result
    except:
        pass
    # TODO database query of the constellation
    return jsonify(ursa_major)


if __name__ == '__main__':
    app.run()
