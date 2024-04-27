let room_id = 0;

// when the user presses the "Enter" key inside of the "message box", 
// the message is sent to the server
$("#message").on("keyup", (e) => {
    if (e.key == "Enter") {
        send(senderusername);
    }
})

$(document).ready(() => {
    // room_id is undefined if the user hasn't joined a room
    // we early return in this case
    if (Cookies.get("room_id") == undefined) {
        return;
    }

    // the user has already joined an existing room
    // we'll display the message box, instead of the "Chat with: " box
    $("#chat_box").hide();
    $("#input_box").show();
    room_id = parseInt(Cookies.get("room_id"));
})

// Here's the Socket IO part of the code
// things get a bit complicated here so brace yourselves :P
let username = "{{ username }}";

Cookies.set('username', username);

// initializes the socket
const socket = io();

// an incoming message arrives, we'll add the message to the message box
socket.on("incoming", (msg, color="orange") => {
    add_message(msg, color);
})

socket.on("public_key_received", (publicKey) => {
    alert("Received public key: " + publicKey);
});



/** This is where we **encrypt** the message
 * @param
 */
async function send(senderUsername) {
    let message = $("#message").val();
    // Fetch the recipient's public key from the server or from a local cache
    let recipientPublicKey = await fetchPublicKey(recipientUsername); TODO //Write this function 

    // Encrypt the message using the recipient's public key
    let encryptedMessage = await encryptMessage(message, recipientPublicKey);

    socket.emit("send", username, message, room_id);  
    $("#message").val("");
} 


async function fetchPublicKey(username) {
    let response = await axios.post("/get_public_key", { username });
    return response.data.public_key;
}


async function encryptMessage(message, recipientPublicKey) {
    // Create an elliptic curve object
    var elliptic = new window.elliptic.ec('secp256k1');

    // Import the recipient's public key
    var key = elliptic.keyFromPublic(recipientPublicKey, 'hex');

    // Generate a shared secret
    var sharedSecret = keyPair.derive(key.getPublic());


    // Encrypt the message using the other symmetric key
    var encryptedMessage = elliptic.ecies.encrypt(publicKey, message);

    return encryptedMessage;
}





// we emit a join room event to the server to join a room
function join_room(receiver) {
   
    socket.emit("join", username, receiver, (res) => {
        // res is a string with the error message if the error occurs
        // this is a pretty bad way of doing error handling, but watevs
        if (typeof res != "number") {
            alert(res);
            return;
        }

        // set the room id variable to the room id returned by the server
        room_id = res;
        Cookies.set("room_id", room_id);

        // now we'll show the input box, so the user can input their message
        $("#chat_box").hide();
        $("#input_box").show();
    });
 
}

// function when the user clicks on "Leave Room"
// emits a "leave" event, telling the server that we want to leave the room
function leave() {
    Cookies.remove("room_id");
    socket.emit("leave", username, room_id);
    $("#input_box").hide();
    $("#chat_box").show();
}

// function to add a message to the message box
// called when an incoming message has reached a client
/**
 * This is where we should use the shared secret to decrypt
 * @param {*} message 
 * @param {*} color 
 */
function add_message(message, color) {
    let box = $("#message_box");
    let child = $(`<p style="color:${color}; margin: 0px;"></p>`).text(message);
    box.append(child);
}

function isSuccessfulAddFriend(string) {
    if (string.startsWith("Successfully ")) {
        return true;
    }
    if (string.startsWith("Error: ")) {
        return false;
    }
    return false;
}

async function addFriend() {
    let friendUsername = $("#friend_username").val();
    let addFriendURL = "{{ url_for('send_friend_request') }}";
    // pass the friend's username and the current user's username to the server
    let res = await axios.post(addFriendURL, {
        friend_username: friendUsername,
        username: Cookies.get('username')
    });
    if (!isSuccessfulAddFriend(res.data)) {
        alert(res.data);
        return;
    }
    alert(`Successfully send friend request to ${friendUsername}.`);
}

async function acceptFriendRequest(friend_id) {
    let acceptFriendRequestURL = "{{ url_for('accept_friend_request') }}";
    let res = await axios.post(acceptFriendRequestURL, {
        username: Cookies.get('username'),
        friend_username: friend_id
    });
    if (res.status == 200) {
        alert(`Successfully accepted friend request from ${friend_id}`);
        // remove the buttons and display the "Approved" status next to the friend request
        $(`#buttons-${friend_id}`).remove();
        $(`#request-${friend_id}`).append('<span> (Approved)</span>');
    } else if (res.status == 404) {
        alert(`Error: Friendship does not exist.`);
    } 
}

async function rejectFriendRequest(friend_id) {
    let rejectFriendRequestURL = "{{ url_for('reject_friend_request') }}";
    let res = await axios.post(rejectFriendRequestURL, {
        username: Cookies.get('username'),
        friend_username: friend_id
    });
    if (res.status == 200) {
        alert(`Successfully rejected friend request from ${friend_id}`);
        $(`#buttons-${friend_id}`).remove();
        $(`#request-${friend_id}`).append('<span> (Rejected)</span>');
    } else if (res.status == 404) {
        alert(`Error: Friendship does not exist.`);
    }
} 

async function refreshFriendRequests() {
    let incomingRequestsURL = "{{ url_for('get_incoming_friend_requests') }}";
    let outgoingRequestsURL = "{{ url_for('get_outgoing_friend_requests') }}";

    let incomingRes = await axios.post(incomingRequestsURL, { username: Cookies.get('username') });
    let outgoingRes = await axios.post(outgoingRequestsURL, { username: Cookies.get('username') });
    
    // clear the table when refresh is clicked
    let table = $("#friend-requests");
    table.empty();
    
    if (outgoingRes.data.no_outgoing_friend_requests) {
        let row = $(`<tr><td>No outgoing friend requests</td><td></td></tr>`);
        table.append(row);
    } else {
        for (let request of outgoingRes.data) {
            let row = $(`<tr><td>${request.friend_id} (${request.status})</td><td></td></tr>`);
            table.append(row);
        }
    }

    if (incomingRes.data.no_incoming_friend_requests) {
        let row = $(`<tr><td></td><td>No incoming friend requests</td></tr>`);
        table.append(row);
    } else {
        // in incoming requests, the user_id field is who sent the request, and the friend_id field is the current user
        for (let request of incomingRes.data) {
            // if the requeste is pending, display the approve and reject buttons
            if (request.status == "pending") {
                let row = $(`<tr><td></td><td id="request-${request.user_id}">${request.user_id} <span id="buttons-${request.user_id}"><button onclick="acceptFriendRequest('${request.user_id}')">Approve</button> <button onclick="rejectFriendRequest('${request.user_id}')">Reject</button></span></td></tr>`);
                table.append(row);
            } else {
                // if the request has been approved or rejected, display the status
                let row = $(`<tr><td></td><td>${request.user_id} (${request.status})</td></tr>`);
                table.append(row);
            }
        }
    }
}

$("#refresh").click(refreshFriendRequests);

// call refreshFriendRequests when the page loads to refresh the friend requests
$(document).ready(refreshFriendRequests);

async function refreshFriends() {
    let friendsURL = "{{ url_for('get_friends') }}";
    let res = await axios.post(friendsURL, { username: Cookies.get('username') });

    let table = $("#friends");
    table.empty();

    if (res.data.no_friends) {
        let row = $(`<tr><td>You don't have any friend yet</td></tr>`);
        table.append(row);
    } else {
        for (let friend of res.data) {
            let row = $(`<tr><td>${friend.friend_id}</td><td><button class="chat-button" data-friend="${friend.friend_id}">Chat</button></td></tr>`);
            table.append(row);
        }
        
        // click event handler for the chat button
        $(".chat-button").click(function() {
            let receiver = $(this).data("friend");
            join_room(receiver);
        });
    }
}

$("#refresh-friends").click(refreshFriends);
$(document).ready(refreshFriends);