from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from __init__ import app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///astropy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Migration configuration
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# Serialisation config
ma = Marshmallow(app)
# app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

""" Models Set up """


class Constellation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    right_ascension = db.Column(db.String(24), nullable=False)
    declination = db.Column(db.String(24), nullable=False)
    quadrant = db.Column(db.String(8), nullable=False)
    min_latitude = db.Column(db.String(4), nullable=False)
    max_latitude = db.Column(db.String(4), nullable=False)


class Stars(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    star = db.Column(db.String(64), nullable=False, unique=True)
    constellation_id = db.Column(db.Integer, db.ForeignKey('constellation.id'))
    constellation = db.relationship('Constellation', backref='stars', lazy=True)

    def __repr__(self):
        return self.name


class StarSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Stars

    # id = ma.auto_field()
    name = ma.auto_field(column_name='star')


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

