'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
import db
from models import *
import secrets
#
import bcrypt
import hmac
import hashlib

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

#By default we use SHA256, but others might be used as well guaranteeing consistency 
def generate_hmac(secret_key: bytes, data: bytes, hash_function=hashlib.sha256) -> str:
    computed_hmac = hmac.new(secret_key, data, hash_function).hexdigest()
    return computed_hmac


def verify_hmac(secret_key: bytes, data: bytes, provided_hmac: str, hash_function=hashlib.sha256) -> bool:
    computed_hmac = generate_hmac(secret_key, data, hash_function)
    """it is recommended to use the compare_digest() function instead of the == operator to reduce the vulnerability to timing attacks."""
    return hmac.compare_digest(computed_hmac, provided_hmac)


def generate_password(unprocessed_password : str) -> bytes:
    """
    Hash and salt a password
    """
    byte : bytes = unprocessed_password.encode('utf-8')
    salt : bytes = bcrypt.gensalt()
    hash : bytes = bcrypt.hashpw(byte, salt)
    return hash

def verify_password(unprocessed_password : str, hash : bytes) -> bool:
    result : bool = bcrypt.checkpw(unprocessed_password, hash)
    return result

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    # retrieve the user name from the JSON data of the POST request
    username = request.json.get("username")
    unprocessed_password : str = request.json.get("password")
    
    # compare it with the user in the database
    user = db.get_user(username)
    if user is None:
        return "Error: User does not exist!"
    if verify_password(unprocessed_password,user.password) != True:
        return "Error: Password does not match!"

    # if the login is successful, returns the url for the home page with the username included as aquery parameter
    return url_for('home', username=request.json.get("username"))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    unnprocessed_password : str = request.json.get("password")
    hashed_password : bytes = generate_password(unnprocessed_password)

    if db.get_user(username) is None:
        db.insert_user(username, hashed_password)
        return url_for('home', username=username)
    return "Error: User already exists."

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)
    return render_template("home.jinja", username=request.args.get("username"))

@app.route("/send_friend_request", methods=["POST"])
def send_friend_request():
    friend_username = request.json.get("friend_username")
    username = request.json.get("username")
    
    if friend_username is None:
        return "Error: The friend field cannot be empty."
    
    if db.get_user(friend_username) is None:
        return f"Error: User [{friend_username}] does not exist."
    
    if db.is_duplicate_friendship(username, friend_username):
        return f"Error: User [{friend_username}] is already your friend or is a pending friend."
    
    db.send_friend_request(username, friend_username)
    return f"Successfully sent friend request to [{friend_username}]."

@app.route("/accept_friend_request", methods=["POST"])
def accept_friend_request():
    user_id = request.json.get("username")
    friend_id = request.json.get("friend_username")
    friendship = db.approve_friend(user_id, friend_id)
    if friendship is None:
        return jsonify({"msg": "Friendship does not exist!"}), 404
    return jsonify({"msg": f"Successfully accepted friend request from [{friend_id}]."}), 200

@app.route("/reject_friend_request", methods=["POST"])
def reject_friend_request():
    user_id = request.json.get("username")
    friend_id = request.json.get("friend_username")
    friendship = db.reject_friend(user_id, friend_id)
    if friendship is None:
        return jsonify({"msg": "Friendship does not exist!"}), 404
    return jsonify({"msg": f"Successfully rejected friend request from [{friend_id}]."}), 200

@app.route("/get_incoming_friend_requests", methods=["POST"])
def get_incoming_friend_requests():
    username = request.json.get("username")
    incoming_friendships = db.fetch_incoming_friend_requests(username)
    # if the incoming_friendships list is either empty or None
    if not incoming_friendships:
        return jsonify({"no_incoming_friend_requests": True})
    # convert the list of friendship objects to a list of dictionaries
    incoming_friendships_json = [f.to_dict() for f in incoming_friendships]
    # parse the list of dictionaries to a json object to the frontend
    return jsonify(incoming_friendships_json)
    
@app.route("/get_outgoing_friend_requests", methods=["POST"])
def get_outgoing_friend_requests():
    username = request.json.get("username")
    outgoing_friendships = db.fetch_outgoing_friend_requests(username)
    if not outgoing_friendships:
        return jsonify({"no_outgoing_friend_requests": True})
    outgoing_friendships_json = [f.to_dict() for f in outgoing_friendships]
    return jsonify(outgoing_friendships_json)

@app.route("/get_friends", methods=["POST"])
def get_friends():
    username = request.json.get("username")
    friendships = db.get_friends(username)
    if not friendships:
        return jsonify({"no_friends": True})
    firends_json = []
    for f in friendships:
        if f.friend_id == username:
            friend_name = f.user_id
            firends_json.append({"friend_id": friend_name})
        if f.user_id == username:
            friend_name = f.friend_id
            firends_json.append({"friend_id": friend_name})
    return jsonify(firends_json)

if __name__ == '__main__':
    ssl_certificate : str = 'certificate.crt'
    ssl_private_key : str = 'private.key'
    socketio.run(app, ssl_context=(ssl_certificate, ssl_private_key))
