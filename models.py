from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Locomotive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50), nullable=False)
    drive_type = db.Column(db.String(20), nullable=False)
    train = db.relationship("Train", backref="locomotive", uselist=False)

class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locomotive_id = db.Column(db.Integer, db.ForeignKey('locomotive.id'))
    wagons = db.relationship("Wagon", backref="train", cascade="all, delete")

    
class Wagon(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    capacity = db.Column(db.Integer, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'))



class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    arrival_time = db.Column(db.String(5))
    departure_time = db.Column(db.String(5))
    order = db.Column(db.Integer, nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'))

Train.stations = db.relationship("Station", backref="train", cascade="all, delete")



class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    ticket = db.relationship("Ticket", backref="passenger", uselist=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    wagon_id = db.Column(db.Integer, db.ForeignKey('wagon.id'))
    passenger_id = db.Column(db.Integer, db.ForeignKey('passenger.id'))
    from_station = db.Column(db.String(50))
    to_station = db.Column(db.String(50))

    wagon = db.relationship("Wagon", backref="tickets")


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
