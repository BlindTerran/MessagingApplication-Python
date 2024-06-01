'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
from db import get_user
from models import *
import secrets

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

# global variable for default theme colour
theme_colour = "black"

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# Knowledge repo page
@app.route("/knowledge_repository")
def knowledge_repository():
    colours = ThemeColour();
    theme_colour = request.args.get("theme_colour")
    # if theme_colour is None:
    #     theme_colour = "black"  
    username = request.args.get("username")
    user = get_user(username)
    print(user)
    print(username)
    print(theme_colour)
    articles = db.get_all_articles()
    return render_template('knowledge_repository.jinja', user=user, username=username, theme_colour=theme_colour, 
                           primary_colour=colours.get_primary_colour(theme_colour), 
                           secondary_colour=colours.get_secondary_colour(theme_colour),
                           font_colour=colours.get_font_colour(theme_colour), articles=articles)

@app.route("/get_current_user", methods=["POST"])
def get_current_user():
    username = request.args.get("username")
    if username:
        return username
    else:
        raise(KeyError)

@app.route("/create_article", methods=["POST"])
def create_article():
    print("create article")
    user = request.json.get("username")
    # print(user)
    # if not user:
    #     return jsonify({"error": "You must be logged in to create an article"}), 401
    # **Handle JSON request**
    data = request.get_json()
    username = data.get("username")
    title = data.get("title")
    content = data.get("content")
    print(username)
    print(title)
    print(content)
    # print("hi")
    db.insert_article(title, content, user)
    return jsonify({"success": True})


@app.route("/edit_article", methods=["POST"])
def edit_article():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to edit an article"}), 401
    # **Handle JSON request**
    data = request.get_json()
    article_id = data.get("article_id")
    title = data.get("title")
    content = data.get("content")
    article = db.get_article(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    if article.author != user.username and not user.is_staff:
        return jsonify({"error": "You do not have permission to edit this article"}), 403
    db.update_article(article_id, title, content)
    return jsonify({"success": True})

@app.route("/delete_article", methods=["POST"])
def delete_article():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to delete an article"}), 401
    # **Handle JSON request**
    data = request.get_json()
    article_id = data.get("article_id")
    article = db.get_article(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    if not user.is_staff:
        return jsonify({"error": "You do not have permission to delete this article"}), 403
    db.delete_article(article_id)
    return jsonify({"success": True})

@app.route("/add_comment", methods=["POST"])
def add_comment():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to add a comment"}), 401
    # **Handle JSON request**
    data = request.get_json()
    article_id = data.get("article_id")
    content = data.get("content")
    db.add_comment(article_id, content, user.username)
    return jsonify({"success": True})

@app.route("/delete_comment", methods=["POST"])
def delete_comment():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to delete a comment"}), 401
    # **Handle JSON request**
    data = request.get_json()
    comment_id = data.get("comment_id")
    comment = db.get_comment(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404
    if not user.is_staff:
        return jsonify({"error": "You do not have permission to delete this comment"}), 403
    db.delete_comment(comment_id)
    return jsonify({"success": True})


# login page
@app.route("/login", methods=["GET"])
def login():    
    theme_colour = request.args.get("themeColour")
    if theme_colour is None:
        theme_colour = "black"
        
    colours = ThemeColour();
    print(theme_colour)
    return render_template("new_login.jinja", theme_colour=theme_colour, 
                           primary_colour=colours.get_primary_colour(theme_colour), 
                           secondary_colour=colours.get_secondary_colour(theme_colour),
                           font_colour=colours.get_font_colour(theme_colour))

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    # retrieve the user name from the JSON data of the POST request
    username = request.json.get("username")
    global current_user
    current_user = username
    password = request.json.get("password")
    theme_colour = request.json.get("themeColour")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if user.password != password:
        return "Error: Password does not match!"
    
    colours = ThemeColour();
    # if the login is successful, returns the url for the home page with aquery parameters, username, theme colours
    return url_for('home', username=request.json.get("username"), theme_colour=theme_colour,
                   primary_colour=colours.get_primary_colour(theme_colour), 
                   secondary_colour=colours.get_secondary_colour(theme_colour),
                   font_colour=colours.get_font_colour(theme_colour))

# handles a get request to the signup page
@app.route("/signup", methods=["GET"])
def signup():
    theme_colour = request.args.get("themeColour")
    if theme_colour is None:
        theme_colour = "black"
    
    colours = ThemeColour();
    return render_template("new_signup.jinja", theme_colour=theme_colour, 
                           primary_colour=colours.get_primary_colour(theme_colour), 
                           secondary_colour=colours.get_secondary_colour(theme_colour),
                           font_colour=colours.get_font_colour(theme_colour))

# TODO: add theme colour 
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")
    theme_colour = request.json.get("themeColour")

    if db.get_user(username) is None:
        db.insert_user(username, password)
        return url_for('home', username=username, theme_colour=theme_colour)
    return "Error: User already exists."

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, the chat page
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)
    username = request.args.get("username")
    theme_colour = request.args.get("theme_colour")
    colours = ThemeColour()
    primary_colour = request.args.get("primary_colour")
    secondary_colour = request.args.get("secondary_colour")
    font_colour = request.args.get("font_colour")
    return render_template("chat.jinja", username=username, theme_colour=theme_colour,
                           primary_colour=colours.get_primary_colour(theme_colour), 
                           secondary_colour=colours.get_secondary_colour(theme_colour),
                           font_colour=colours.get_font_colour(theme_colour))

@app.route("/chat")
def chat():
    username = request.args.get("username")
    theme_colour = request.args.get("theme_colour")
    if username is None:
        abort(404)
    colours = ThemeColour()
    return render_template("chat.jinja", username=username, theme_colour=theme_colour, 
                           primary_colour=colours.get_primary_colour(theme_colour),
                            secondary_colour=colours.get_secondary_colour(theme_colour),
                            font_colour=colours.get_font_colour(theme_colour))

@app.route("/friends")
def friends():
    username = request.args.get("username")
    theme_colour = request.args.get("theme_colour")
    if username is None:
        abort(404)
    colours = ThemeColour()
    return render_template("friends.jinja", username=username, theme_colour=theme_colour, 
                           primary_colour=colours.get_primary_colour(theme_colour), 
                           secondary_colour=colours.get_secondary_colour(theme_colour),
                           font_colour=colours.get_font_colour(theme_colour))

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
    return jsonify(incoming_friendships_json), 200
    
@app.route("/get_outgoing_friend_requests", methods=["POST"])
def get_outgoing_friend_requests():
    username = request.json.get("username")
    outgoing_friendships = db.fetch_outgoing_friend_requests(username)
    if not outgoing_friendships:
        return jsonify({"no_outgoing_friend_requests": True})
    outgoing_friendships_json = [f.to_dict() for f in outgoing_friendships]
    return jsonify(outgoing_friendships_json), 200

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
    return jsonify(firends_json), 200

@app.route("/remove_friend", methods=["POST"])
def remove_friend():
    username = request.json.get("username")
    friend_username = request.json.get("friend_username")
    try:
        db.remove_friend(username, friend_username)
        return jsonify({"msg": f"Successfully removed friend."}), 200
    except ValueError as e:
        return jsonify({"msg": str(e)}), 404
    
@app.route("/get_active_chats", methods=["POST"])
def get_active_chats():
    username = request.json['username']
    active_chats = db.get_active_chats(username)
    if not active_chats:
        return jsonify({"no_active_chats": True})
    active_chats_json = []
    for chat_room in active_chats:
        active_chats_json.append(chat_room.to_dict())
    return jsonify(active_chats_json), 200

@app.route("/get_friends_except_current_friend", methods=["POST"])
def get_friends_except_current_friend():
    username = request.json.get("username")
    friend_username = request.json.get("friend_username")
    friends = db.get_friends_except_current_friend(username, friend_username)
    if not friends:
        return jsonify({"no_friends": True})
    return jsonify({"friends": friends}), 200

@app.route("/is_group_chat", methods=["POST"])
def is_group_chat():
    chatroom_id = request.json.get("chatroom_id")
    is_group_chat = db.is_group_chat(chatroom_id)
    if is_group_chat is None:
        return jsonify({"msg": "Failed to fetch chatroom info."}), 404
    return jsonify({"is_group_chat": is_group_chat}), 200

@app.route("/get_receiver_from_chat", methods=["POST"])
def get_receiver_from_chat():
    chatroom_id = request.json.get("chatroom_id")
    username = request.json.get("username")
    receiver_id = db.get_receiver_from_chat(chatroom_id, username)
    if receiver_id is None:
        return jsonify({"msg": "Receiver not found."}), 404
    user = db.get_user(receiver_id)
    return jsonify(user.to_dict()), 200

@app.route("/get_friends_not_in_group_chat", methods=["POST"])
def get_friends_not_in_group_chat():
    username = request.json.get("username")
    chatroom_id = request.json.get("chatroom_id")
    # a list of friend names that are not in the target group chat
    friends = db.get_friends_not_in_group_chat(username, chatroom_id)
    if not friends:
        return jsonify({"no_friends_not_in_group_chat": True})
    return jsonify({"friends": friends}), 200

# get members except the current user
@app.route("/get_group_chat_members", methods=["POST"])
def get_group_chat_members():
    chatroom_id = request.json.get("chatroom_id")
    username = request.json.get("username")
    # a list of member names
    members = db.get_group_chat_members(chatroom_id, username)
    if not members:
        return jsonify({"no_members": True})
    return jsonify({"members": members}), 200

@app.route("/get_group_chats", methods=["POST"])
def get_group_chats():
    username = request.json.get("username")
    group_chats = db.get_group_chats(username)
    if not group_chats:
        return jsonify({"no_group_chats": True})
    group_chats_json = []
    for chat_room in group_chats:
        group_chats_json.append(chat_room.to_dict())
    return jsonify(group_chats_json), 200

    
# ==================== TEST PAGE ====================
# return the page jinja file you want to test
# this method will be invoked by the button in sign up page
# @app.route('/test_page')
# def test_page():
#     colours = ThemeColour()
#     username = "tim" # log in as which user, for testing purposes
#     # return the target page you want to test
#     return render_template('friends.jinja', username=username, primary_colour=colours.get_primary_colour(theme_colour), 
#                            secondary_colour=colours.get_secondary_colour(theme_colour),
#                            font_colour=colours.get_font_colour(theme_colour))

if __name__ == '__main__':
    socketio.run(app, debug=True)
