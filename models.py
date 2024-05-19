'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import Column, Table, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Dict
import sqlalchemy
import db

# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    is_online: Mapped[bool] = mapped_column(sqlalchemy.Boolean, default=False)
    permission: Mapped[int] = mapped_column(sqlalchemy.Integer) #~
    """0 = student, 1 = academics, 2 = staff, 3 = admin"""
    
    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "is_online": self.is_online,
            "permission": self.permission
        }

class Article(Base):
    __tablename__ = 'articles'
    id : Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    title : Mapped[str] = mapped_column(String)
    content : Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String, ForeignKey('user.username'), primary_key=True)
    comments: Mapped[str] = mapped_column(sqlalchemy.Integer, ForeignKey('comments.id'), primary_key=True)

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(sqlalchemy.Integer, primary_key=True)
    content : Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String, ForeignKey('user.username'), primary_key=True)
    article_id: Mapped[int] = mapped_column(sqlalchemy.Integer, ForeignKey('articles.id'), primary_key=True)

# relative entity to store the friendship between user and user
class Friendship(Base):
    __tablename__ = "friendship"
    
    # the combination of user_id and friend_id is the primary key, they have to be unique in this table
    user_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'), primary_key=True)
    friend_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'), primary_key=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status
        }
        
class Chatroom(Base):
    __tablename__ = "chatroom"
    
    chatroom_id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    chatroom_name: Mapped[str] = mapped_column(String)
    
    def to_dict(self):
        return {
            "chatroom_id": self.chatroom_id,
            "chatroom_name": self.chatroom_name
        }
    
class UserGroup(Base):
    __tablename__ = "user_group"

    group_id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    chatroom_id: Mapped[int] = mapped_column(sqlalchemy.Integer, ForeignKey('chatroom.chatroom_id'))    
    user_id: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    
class Message(Base):
    __tablename__ = "message"
    
    message_id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    chatroom_id: Mapped[int] = mapped_column(sqlalchemy.Integer, ForeignKey('chatroom.chatroom_id'))
    sender: Mapped[str] = mapped_column(String, ForeignKey('user.username'))
    message: Mapped[str] = mapped_column(String)
    
    def to_dict(self):
        return {
            "message_id": self.message_id,
            "chatroom_id": self.chatroom_id,
            "sender": self.sender,
            "message": self.message
        }
        
class Counter(Base):
    __tablename__ = "counter"
    
    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    room_counter: Mapped[int] = mapped_column(sqlalchemy.Integer, default=0)
    user_group_counter: Mapped[int] = mapped_column(sqlalchemy.Integer, default=0)
    message_counter: Mapped[int] = mapped_column(sqlalchemy.Integer, default=0)
    
    
# stateful counter used to generate the room id
# class Counter():
#     def __init__(self):
#         self.counter = 0
    
#     def get(self):
#         self.counter += 1
#         return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
class ThemeColour():
    def __init__(self):
        self.primary_colours: dict = {
            "black": "#000000", # black
            "blue": "#007aff", # blue
            "guava": "#ff2d55" # red
        }
        self.secondary_colours: dict = {
            "black": "#d3d3d3", # grey
            "blue": "#aad3ff", # light blue
            "guava": "#ffbeba", # light red
        }
        self.tertiary_colours: dict = {
            "black": "#f2f2f2", # light grey
            "blue": "#f2f2f2", 
            "guava": "#f2f2f2"
        }
        self.font_colours: dict = {
            "black": "#ffffff", # white
            "blue": "#ffffff",
            "guava": "#ffffff"
        }
    
    def get_primary_colour(self, colour):
        return self.primary_colours[colour]
    
    def get_secondary_colour(self, colour):
        return self.secondary_colours[colour]
    
    def get_font_colour(self, colour):
        return self.font_colours[colour]
    
    