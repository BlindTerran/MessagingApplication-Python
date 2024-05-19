$(document).ready(function() {
    // set the username in the cookie
    let username = "{{ username }}";
    Cookies.set('username', username);

    // refresh the active chats
    refreshActiveChats();

    // reset some cookie data every time the page is load
    Cookies.remove('roomId');
    Cookies.remove('receiverName');

    // don't show the send button and message input when user hasn't selected a chat
    let roomId = Cookies.get('roomId');
    if (!roomId) {
        $('#chat-title').html("Select a chat to start chatting");
        $('#send-button').hide();
        $('#message-input').hide();
        $('#friends-container').hide();
        $('#add-friend-to-group-chat-container').hide();
        $('#group-chat-members-container').hide();
    }
});

// initalise the socket, this will invoke the connect function in socket_routes.py
const socket = io();

// listen for incoming message
socket.on("incoming", (msg, colour="black") => {
    addMessage(msg, colour);
})

function send() {
    let message = $("#message-input").val();
    $("#message-input").val("");
    let username = Cookies.get('username');
    let roomId = Cookies.get('roomId');
    if (message.trim() == "") {
        alert("Message cannot be empty");
    } else {
        socket.emit("send", username, message, roomId);
    }
}

$("#send-button").click(function() {
    send();
});

function addMessage(message, color) {
    let messageElement = $(`<div class="message" style="color: ${color};">${message}</div>`);
    $(".main-content-container").append(messageElement);
}

// empty the main content section when the page is loaded
// an active chat is a chatroom that the user has joined
async function refreshActiveChats() {
    let activeChatsURL = "{{ url_for('get_active_chats') }}";
    let res = await axios.post(activeChatsURL, { username: Cookies.get('username') });

    let container = $("#active-chats-container");
    container.empty();

    if (res.data.no_active_chats) {
        let row = $(`<div>No active chats yet</div>`);
        container.append(row);
    } else {
        for (let chat of res.data) {
            let chatElement = $(`<div class="chat">${chat.chatroom_name}</div>`);
            chatElement.data('chat', chat);
            container.append(chatElement);
        }
    }
}

// click an active chat to initiate a chat
// this function joins the chat room with the target user or group chat, and
// displays receiver's info or group name in the secondary banner, and
// loads history message to the main content container, and
// loads the create group chat to the right side card if it is a private chat, or
// loads group chat members and add friends to group chat if it is a group chat
let currentRoomId = Cookies.get('roomId');
$("#active-chats-container").on('click', '.chat', function() {
    // leave the current chat room if there is one
    if (currentRoomId) {
        socket.emit("leave", currentRoomId);
    }
    
    let chat = $(this).data('chat');
    // store the chatroom id in the cookie
    // user can now send messages to this chatroom
    Cookies.set('roomId', chat.chatroom_id);

    // display the chat title
    // check if the chat is a group chat or not
    let isGroupChatURL = "{{ url_for('is_group_chat') }}";
    axios.post(isGroupChatURL, { chatroom_id: chat.chatroom_id })
        .then(res => {
            if (res.status == 200) {
                let isGroupChat = res.data.is_group_chat;

                // TODO: if it is a group chat, display the chatroom name as the chat title
                // display group related info in the right side card
                // TODO: display group chat members and add friends to group chat
                if (isGroupChat) {
                    $('#chat-title').html(`${chat.chatroom_name}`);
                    refreshGroupChatMembers();
                    $('#group-chat-members-container').show();
                    refreshFriendsNotInGroupChat();
                    $('#add-friend-to-group-chat-container').show();

                } else {
                    // if it is a private chat, display the receiver's name and online status
                    let getReceiverNameURL = "{{ url_for('get_receiver_from_chat') }}";
                    axios.post(getReceiverNameURL, { chatroom_id: chat.chatroom_id, username: Cookies.get('username') })
                        .then(res => {
                            if (res.status == 200) {
                                let receiverName = res.data.username;
                                let onlineStatus = res.data.is_online;
                                let statusIndicator = onlineStatus ? '<span class="user-online-indicator"></span>' : '<span class="user-offline-indicator"></span>';
                                $('#chat-title').html(`${statusIndicator} ${receiverName}`);

                                // loads the create group chat to the right side card
                                Cookies.set('receiverName', receiverName);
                                refreshFriends(receiverName);
                                $('#friends-container').show();

                                // auto refresh the friends every 2 seconds
                                setInterval(() => refreshFriends(receiverName), 2000);
                            } else if (res.status == 404) {
                                // can't find the receiver 
                                alert(res.data.msg);
                            }
                        })
                }
            } else if (res.status == 404) {
                // can't find the chat room or other query error
                alert(res.data.msg);
            }
        })

    // prepare the main content container to display the messages
    // fetch messages, and join the room, done in fetch_message function
    let mainContent = $(".main-content-container");
    mainContent.empty();
    socket.emit("fetch_message", chat.chatroom_id);

    $('#send-button').show();
    $('#message-input').show();
});
// auto refresh the active chats every 2 seconds
setInterval(refreshActiveChats, 2000);

// get a list of friends except the friend in the current chat 
async function refreshFriends(friend_username) {
    let friendsURL = "{{ url_for('get_friends_except_current_friend') }}";
    let res = await axios.post(friendsURL, { username: Cookies.get('username'), friend_username });

    let container = $("#friends-container");
    container.empty();

    if (res.data.no_friends) {
        let row = $(`<div>No friends can be added yet</div>`);
        container.append(row);
    } else {
        for (let friend of res.data.friends) {
            let friendElement = $(`<div class="friend">${friend} <button class="add-friend-btn" data-friend-id="${friend}">Add</button></div>`);
            container.append(friendElement);
        }
    }

    $(".add-friend-btn").click(function() {
        let friendToAddId = $(this).data("friend-id");
        let username = Cookies.get('username');
    
        socket.emit("create_group_chat", friendToAddId, username, friend_username); // param: friend to add, current user, friend in the current chat
        alert("Group chat created contains you, " + friendToAddId + ", and " + friend_username);
    });
}    

async function refreshFriendsNotInGroupChat() {
    let friendsURL = "{{ url_for('get_friends_not_in_group_chat') }}";
    let res = await axios.post(friendsURL, { username: Cookies.get('username'), chatroom_id: Cookies.get('roomId')});

    let container = $("#add-friend-to-group-chat-container");
    container.empty();

    if (res.data.no_friends_not_in_group_chat) {
        let row = $(`<div>No friends can add to group</div>`);
        container.append(row);
    } else {
        for (let friendName of res.data.friends) {
            let friendElement = $(`<div class="friend">${friendName} <button class="add-friend-to-group-btn" data-friend-id="${friendName}">Add</button></div>`);
            container.append(friendElement);
        }
    }

    $(".add-friend-to-group-btn").click(function() {
        let friendId = $(this).data("friend-id");
        let roomId = Cookies.get('roomId');
    
        socket.emit("add_friend_to_group_chat", friendId, roomId);
        alert(friendId + " is added to the group chat.");
    });
}
setInterval(refreshFriendsNotInGroupChat, 2000);

// get a list of group chat members except the current user
async function refreshGroupChatMembers() {
    let groupChatMembersURL = "{{ url_for('get_group_chat_members') }}";
    let res = await axios.post(groupChatMembersURL, { chatroom_id: Cookies.get('roomId'), username: Cookies.get('username')});

    let container = $("#group-chat-members-container");
    container.empty();

    if (res.data.no_members) {
        let row = $(`<div>Failed to find group members</div>`);
        container.append(row);
    } else {
        for (let member of res.data.members) {
            let memberElement = $(`<div class="group-member">${member}</div>`);
            container.append(memberElement);
        }
    }
}
setInterval(refreshGroupChatMembers, 2000);
