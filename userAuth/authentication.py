import hashlib 
import getpass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    pass

def login(username, passowrd):
    pass