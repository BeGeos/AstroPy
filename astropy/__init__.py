from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# App configuration
app = Flask(__name__)
app.config['DEBUG'] = True

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///astropy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Output Schema configuration
# app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

# Database init
db = SQLAlchemy(app)

from . import astroAPI



