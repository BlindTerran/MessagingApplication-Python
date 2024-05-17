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

# Base.metadata.drop_all(engine, [Counter.__table__])
# Base.metadata.create_all(engine, [Counter.__table__])

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
    
def get_user_status(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.is_online

def set_user_status(username: str, status: bool):
    with Session(engine) as session:
        user = session.get(User, username)
        user.is_online = status
        session.commit()

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
    
def remove_friend(username: str, friend_username: str):
    with Session(engine) as session:
        friendship = session.query(Friendship).filter(
            ((Friendship.user_id == username) & (Friendship.friend_id == friend_username)) | 
            ((Friendship.user_id == friend_username) & (Friendship.friend_id == username))
        ).first()
        if friendship is None:
            raise ValueError(f"No friendship between {username} and {friend_username}")
        session.delete(friendship)
        session.commit()

def get_room_counter():
    with Session(engine) as session:
        counter = session.query(Counter).first()
        if counter is None:
            counter = Counter(room_counter=0)
            session.add(counter)
            session.commit()
        counter.room_counter += 1
        session.commit()
        return counter.room_counter

def get_user_group_counter():
    with Session(engine) as session:
        counter = session.query(Counter).first()
        if counter is None:
            counter = Counter(user_group_counter=0)
            session.add(counter)
            session.commit()
        counter.user_group_counter += 1
        session.commit()
        return counter.user_group_counter
    
def get_message_counter():
    with Session(engine) as session:
        counter = session.query(Counter).first()
        if counter is None:
            counter = Counter(message_counter=0)
            session.add(counter)
            session.commit()
        counter.message_counter += 1
        session.commit()
        return counter.message_counter
    
def get_private_chatroom_id(user1: str, user2: str):
    with Session(engine) as session:
        # get the chatrooms that user1 and user2 are in
        user1_rooms = session.query(UserGroup.chatroom_id).filter(UserGroup.user_id == user1).subquery().select()
        user2_rooms = session.query(UserGroup.chatroom_id).filter(UserGroup.user_id == user2).subquery().select()
        if user1_rooms is None or user2_rooms is None:
            return None
        
        # get the chatrooms that only contains 2 users (private chatroom)
        rooms_contains_two_users = session.query(UserGroup.chatroom_id).group_by(UserGroup.chatroom_id).having(
            sqlalchemy.func.count(UserGroup.user_id) == 2
        ).subquery()
        if rooms_contains_two_users is None:
            return None
        
        # get the private chatroom that contains both user1 and user2
        private_chatroom = session.query(rooms_contains_two_users.c.chatroom_id).filter(
            rooms_contains_two_users.c.chatroom_id.in_(user1_rooms),
            rooms_contains_two_users.c.chatroom_id.in_(user2_rooms)
        ).first()
        return private_chatroom[0] if private_chatroom is not None else None

def get_friends_except_current_friend(username: str, friend_id: str):
    with Session(engine) as session:
        friends = session.query(Friendship).filter(
            ((Friendship.user_id == username) | (Friendship.friend_id == username)) & (Friendship.status == 'accepted')
        ).all()
        friends_except_current_friend = []
        for f in friends:
            if f.user_id == username:
                friend = f.friend_id
            else:
                friend = f.user_id
            if friend != friend_id:
                friends_except_current_friend.append(friend)
        return friends_except_current_friend

def get_receiver_from_chat(chatroom_id: int, sender: str):
    with Session(engine) as session:
        user_group = session.query(UserGroup).filter(UserGroup.chatroom_id == chatroom_id).filter(UserGroup.user_id != sender).first()
        return user_group.user_id

def is_group_chat(chatroom_id: int):
    with Session(engine) as session:
        user_group = session.query(UserGroup).filter(UserGroup.chatroom_id == chatroom_id).all()
        return len(user_group) > 2

def get_friends_not_in_group_chat(chatroom_id: int, username: str):
    with Session(engine) as session:
        user_group = session.query(UserGroup).filter(UserGroup.chatroom_id == chatroom_id).all()
        friends = session.query(Friendship).filter(
            ((Friendship.user_id == username) | (Friendship.friend_id == username)) & (Friendship.status == 'accepted')
        ).all()
        friends_not_in_chat = []
        for f in friends:
            if f.user_id == username:
                friend = f.friend_id
            else:
                friend = f.user_id
            if friend not in [u.user_id for u in user_group]:
                friends_not_in_chat.append(friend)
        # a list of friend names that are not in the chatroom
        return friends_not_in_chat

def add_user_to_group_chat(username: str, chatroom_id: int):
    with Session(engine) as session:
        user_group = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom_id, user_id=username)
        session.add(user_group)
        session.commit()

def create_private_chat_room(user1: str, user2: str):
    with Session(engine) as session:
        chatroom = Chatroom(chatroom_id=get_room_counter(), chatroom_name=f"{user1} and {user2}")
        session.add(chatroom)
        session.commit()
        
        user_group1 = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom.chatroom_id, user_id=user1)
        user_group2 = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom.chatroom_id, user_id=user2)
        session.add(user_group1)
        session.add(user_group2)
        session.commit()
        return chatroom.chatroom_id

def create_group_chat_room(user1: str, user2: str, user3: str):
    with Session(engine) as session:
        chatroom_id = get_room_counter()
        chatroom = Chatroom(chatroom_id=chatroom_id, chatroom_name=f"Group {user1} {chatroom_id}")
        session.add(chatroom)
        session.commit()
        
        user_group1 = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom.chatroom_id, user_id=user1)
        user_group2 = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom.chatroom_id, user_id=user2)
        user_group3 = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom.chatroom_id, user_id=user3)
        session.add(user_group1)
        session.add(user_group2)
        session.add(user_group3)
        session.commit()
        return chatroom.chatroom_id

# get all the members of a group chat except the current user
def get_group_chat_members(chatroom_id: int, username: str):
    with Session(engine) as session:
        user_group = session.query(UserGroup).filter(UserGroup.chatroom_id == chatroom_id).all()
        members = []
        for u in user_group:
            if u.user_id != username:
                members.append(u.user_id)
        return members

def add_user_to_group_chat(chatroom_id: int, user: str):
    with Session(engine) as session:
        user_group = UserGroup(group_id=get_user_group_counter(), chatroom_id=chatroom_id, user_id=user)
        session.add(user_group)
        session.commit()

def get_active_chats(username: str):
    with Session(engine) as session:
        chatrooms = session.query(Chatroom).join(UserGroup).filter(UserGroup.user_id == username).all()
        return chatrooms
    
def store_message(chatroom_id: int, sender: str, message: str):
    with Session(engine) as session:
        message = Message(
            message_id=get_message_counter(),
            chatroom_id=chatroom_id,
            sender=sender,
            message=message
        )
        session.add(message)
        session.commit()

def fetch_messages(chatroom_id: int):
    with Session(engine) as session:
        messages = session.query(Message).filter(Message.chatroom_id == chatroom_id).all()
        return messages