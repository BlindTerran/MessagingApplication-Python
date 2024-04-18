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

# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

# adds a friend to the user
def add_friend(username: str, friend_username: str):
    with Session(engine) as session:
        friendship = Friendship(user_id=username, friend_id=friend_username)
        session.add(friendship)
        session.commit()
        
def is_duplicate_friendship(username: str, friend_username: str):
    with Session(engine) as session:
        firendship = session.query(Friendship).filter(
            ((Friendship.user_id == username) & (Friendship.friend_id == friend_username)) | 
            ((Friendship.user_id == friend_username) & (Friendship.friend_id == username))
        ).first() 
        # if the friendship already exists in the database, return true
        if firendship is not None:
            return True
        return False