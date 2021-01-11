from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from __init__ import app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

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


class AuthKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String(24))
    expiration_date = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return self.key


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
