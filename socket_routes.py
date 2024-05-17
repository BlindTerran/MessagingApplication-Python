'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('get_status')
def get_status(username):
    if username is None:
        return
    return db.get_user_status(username)

@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    db.set_user_status(username, True)

# automatically called when the user disconnects, close the browser tab, etc
@socketio.on('disconnect')
def disconnect():    
    username = request.cookies.get("username")
    db.set_user_status(username, False)

# send message event handler
@socketio.on("send")
def send(username, message, room_id):
    join_room(room_id)
    db.store_message(room_id, username, message)
    emit("incoming", (f"{username}: {message}"), to=int(room_id))
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = db.get_private_chatroom_id(sender_name, receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        join_room(room_id)

    # if the user isn't inside of any room, create new room
    room_id = db.create_private_chat_room(sender_name, receiver_name)
    join_room(room_id)
    emit("incoming", (f"{sender_name} has established a communication with {receiver_name}.", "green"), to=room_id)
    return room_id

@socketio.on("create_group_chat")
def create_group_chat(friend_id, username, friend_id_2):
    room_id = db.create_group_chat_room(username, friend_id, friend_id_2)
    join_room(room_id)
    return room_id

@socketio.on("add_friend_to_group_chat")
def add_friend_to_group_chat(friend_id, room_id):
    db.add_user_to_group_chat(friend_id, room_id)

# leave room event handler
@socketio.on("leave")
def leave(room_id):
    # emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)

@socketio.on("fetch_message")
def fetchMessage(room_id):
    join_room(room_id)
    messages = db.fetch_messages(room_id)
    for message in messages:
        emit("incoming", (f"{message.sender}: {message.message}"), to=request.sid)
