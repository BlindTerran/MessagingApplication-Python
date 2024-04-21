## Public-private key encryption for message exchange
1. **generate key pair for user** 
Generate key pair upon user signup, this is to ensure the key-pair is persistent and a user does not have their key-pair changed at any given future time
2. **Store user public key in database**
after the user signed up, their public key is send to the server side and stored in the database permanently, an `public_key` attribute is added to the `User` table in the relational database
3. **Store user private key in secure cookie**
Secure cookie is a cookie with HttpOnly attribute, it can only be accessed via HTTPS (in our project the HTTPS is grounded, this makes secure cookie possible) and is inaccessible by JavaScript, which makes data inside the secure cookie resilient in XXS attack.
The client generates the private key and it is securely send over to the server side via HTTPS, and the server set the private key to the secure cookie and the secure cookie is sent back to client in the `response` .
```python
@app.route("/signup/user", methods=["POST"])
def signup_user():
	if not request.is_json:
		abort(404)
		
	username = request.json.get("username")
	password = request.json.get("password")
	public_key = request.json.get("public_key")
	private_key = request.json.get("private_key")
	
	#...
	
	# the response returned to the client side contains the redirection to the user page
	response = make_response(url_for('home', username=username))
	
	# set the private key as a secure httponly cookie
	response.set_cookie("privateKey", private_key, secure=True, httponly=True)
```