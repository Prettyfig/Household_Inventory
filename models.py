from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class StorageBin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text)
    qr_code_filename = db.Column(db.String(120))
    items = db.relationship('InventoryItem', backref='bin', lazy='dynamic', cascade="all, delete-orphan")
    color = db.Column(db.String(7))  # e.g. "#aabbcc"

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    notes = db.Column(db.String(255))
    photo_filename = db.Column(db.String(255))
    bin_id = db.Column(db.Integer, db.ForeignKey('storage_bin.id'))

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    color = db.Column(db.String(7))  # e.g. "#aabbcc"
