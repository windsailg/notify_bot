from flask import Flask, jsonify
from route import register_routes

app = Flask(__name__)

if __name__ == '__main__':
    register_routes(app)
    app.run(debug=True)