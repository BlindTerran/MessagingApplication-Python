const crypto = require('crypto');



function isValidURL(string) {
    if (string.length == 0) {
        return false;
    }
    if (string[0] == "/") {
        return true;
    }
    return false;
}

// this function is identical to login(), see login.jinja
async function signup() {
    userA = crypto.createECDH('secp256k1');
    userAPublicKey = userA.getPublicKey().toString('base64');
    let loginURL = "{{ url_for('signup_user') }}";
    let res = await axios.post(loginURL, {
        username: $("#username").val(),
        password: $("#password").val(),
        public_key: userAPublicKey
    });
    if (!isValidURL(res.data)) {
        alert(res.data);
        return;
    }
    window.open(res.data, "_self")
}