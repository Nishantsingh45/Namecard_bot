from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Change to Integer with autoincrement
    phone = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String)
    image = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contacts = db.relationship('ContactInfo', backref='user', lazy=True)

class ContactInfo(db.Model):
    __tablename__ = 'contact_infos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Change to Integer with autoincrement
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    phone_number = db.Column(db.String)
    company = db.Column(db.String)
    position = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)