'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# Base.metadata.drop_all(engine, [Friendship.__table__])
# Base.metadata.create_all(engine, [Friendship.__table__])

# inserts a user to the database

def insert_message(sender_id : str, receiver_id : str, encryped_message : str):
    with Session(engine) as session:
        message : Conversation = Conversation(sender_id=sender_id, receiver_id=receiver_id, encryped_message=encryped_message)
        session.add(message)
        session.commit()

def get_message(reader_id : str):
    #TODO #TODO
    # I suppose both the sender and the reciver are primary so
    # This should get all messages available
    with Session(engine) as session:
        message = session.query(Conversation).filter(
            (Conversation.sender_id == reader_id) |
            (Conversation.receiver_id == reader_id)
        )#.first()
        return message
    

def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

def send_friend_request(username: str, friend_username: str):
    with Session(engine) as session:
        friendship = Friendship(user_id=username, friend_id=friend_username, status="pending")
        session.add(friendship)
        session.commit()

def approve_friend(username: str, friend_username: str):
    with Session(engine) as session:
        friendship = session.query(Friendship).filter(
            (Friendship.user_id == friend_username) & (Friendship.friend_id == username) |
            (Friendship.user_id == username) & (Friendship.friend_id == friend_username)
        ).first()
        friendship.status = "accepted"
        session.commit()
        return friendship
        
def reject_friend(username: str, friend_username: str):
    with Session(engine) as session:
        friendship = session.query(Friendship).filter(
            (Friendship.user_id == friend_username) & (Friendship.friend_id == username) |
            (Friendship.user_id == username) & (Friendship.friend_id == friend_username)
        ).first()
        friendship.status = "rejected"
        session.commit()
        return friendship
        
def fetch_incoming_friend_requests(username: str):
    with Session(engine) as session:
        incoming_friend_requests = session.query(Friendship).filter(
            # fetch all incoming friendships either pending or rejected
            (Friendship.friend_id == username) & (Friendship.status != "approved")
            ).all()
        return incoming_friend_requests
    
def fetch_outgoing_friend_requests(username: str):
    with Session(engine) as session:
        outgoing_friend_requests = session.query(Friendship).filter(
            (Friendship.user_id == username) & (Friendship.status != "approved")
            ).all()
        return outgoing_friend_requests
        
# if a friendship already exists in the database, AND it is not rejected, return True, false otherwise
def is_duplicate_friendship(username: str, friend_username: str):
    with Session(engine) as session:
        firendship = session.query(Friendship).filter(
            ((Friendship.user_id == username) & (Friendship.friend_id == friend_username)) | 
            ((Friendship.user_id == friend_username) & (Friendship.friend_id == username))
        ).all() 
        for f in firendship:
            if f.status != "rejected":
                return True
        return False

# get all the friends of a user, a friend is a user that has accepted the friendship request
def get_friends(username: str):
    with Session(engine) as session:
        friends = session.query(Friendship).filter(
            ((Friendship.user_id == username) | (Friendship.friend_id == username)) &
            (Friendship.status == "accepted")
        ).all()
        return friends