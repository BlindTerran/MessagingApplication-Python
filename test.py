from flask import Flask

app = Flask(__name__)

# Route for the home page
@app.route('/')
def index():
    return 'Hello, HTTPS!'

if __name__ == '__main__':
    # Specify the paths to your SSL certificate and private key
    ssl_cert = 'path/to/your/certificate.crt'
    ssl_key = 'path/to/your/private.key'

    # Run Flask application with HTTPS enabled
    app.run(debug=True, ssl_context=(ssl_cert, ssl_key))
