from flask_login import UserMixin
from models import User

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "admin"
        self.password = "password"  # Change this in production!