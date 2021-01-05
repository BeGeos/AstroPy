from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from __init__ import app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime

# Database init
db = SQLAlchemy(app)

# Migration configuration
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# Serialisation configuration
ma = Marshmallow(app)


# Models Setup
class Constellation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    right_ascension = db.Column(db.String(24), nullable=False)
    declination = db.Column(db.String(24), nullable=False)
    quadrant = db.Column(db.String(8), nullable=False)
    min_latitude = db.Column(db.Integer, nullable=False)
    max_latitude = db.Column(db.Integer, nullable=False)
    best_seen = db.Column(db.String(8))


class Stars(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    star = db.Column(db.String(64), nullable=False, unique=True)
    right_ascension = db.Column(db.String(24))
    declination = db.Column(db.String(24))
    type = db.Column(db.String(24))
    app_magnitude = db.Column(db.Float)
    distance = db.Column(db.Float)
    constellation_id = db.Column(db.Integer, db.ForeignKey('constellation.id'))
    constellation = db.relationship('Constellation', backref='stars', lazy=True)

    def __repr__(self):
        return self.name


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128))
    calls = db.Column(db.Integer, default=1000)
    attempts = db.Column(db.Integer, default=5)
    confirmed = db.Column(db.Boolean, default=False)
    auth_key = db.relationship('AuthKeys', backref='user', lazy=True, uselist=False)
    security_code = db.relationship('SecurityCodes', backref='user', lazy=True, uselist=False)
    recovery = db.relationship('Recovery', backref='user', lazy=True, uselist=False)
    date_created = db.Column(db.DateTime)

    def __repr__(self):
        return self.username


class AuthKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(24))
    expiration_date = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.key


# Security models
class SecurityCodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.Integer, nullable=False)
    expiration = db.Column(db.Integer)


# -- Recover password
class Recovery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_extension = db.Column(db.String(24))
    exp_date = db.Column(db.Integer)

    def __repr__(self):
        return f'http://localhost:5000/{self.url_extension}'


# Schema Setup
class StarSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Stars

    # id = ma.auto_field()
    name = ma.auto_field(column_name='star')
    apparent_magnitude = ma.auto_field(column_name='app_magnitude')


class SingleConstellationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Constellation

    name = ma.auto_field()


class SingleStarSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Stars

    name = ma.auto_field(column_name='star')
    right_ascension = ma.auto_field()
    declination = ma.auto_field()
    apparent_magnitude = ma.auto_field(column_name='app_magnitude')
    distance = ma.auto_field()
    type = ma.auto_field()
    constellation = fields.Nested(SingleConstellationSchema())


class ConstellationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Constellation

    id = ma.auto_field()
    name = ma.auto_field()
    right_ascension = ma.auto_field()
    declination = ma.auto_field()
    quadrant = ma.auto_field()
    min_latitude = ma.auto_field()
    max_latitude = ma.auto_field()
    stars = fields.Nested(StarSchema(many=True))


if __name__ == '__main__':
    manager.run()
