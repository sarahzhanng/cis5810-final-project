from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
import time
import threading
import requests

app = Flask(__name__)
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["cis-5810"]
users_collection = db["users"]
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.json

    existing_user = users_collection.find_one({'username': data['username']})
    if existing_user:
        return jsonify({"message": "Username already exists"}), 409
    
    users_collection.insert_one({
        'username': data['username'],
        'password': data['password'],
    })
    return jsonify({'message': 'Signup Successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users_collection.find_one({'username': data['username']})
    
    if user['password'] != data['password']: 
        jsonify({"message": "Incorrect username or password"}), 401
        
    resp = make_response(jsonify({'message': 'Login Successful'}), 201)
    resp.set_cookie(
        "token",
        "example_jwt_token",
        httponly=True,
        samesite="None",
        secure=True
    )
    return resp
@app.route('/me')
def me():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"loggedIn": False})

    return jsonify({"loggedIn": True, "token": token})

# SocketIO event
@socketio.on('send_message')
def handle_message(data):
    msg = data.get('message', '')
    print(f"Received from client: {msg}")
    emit('receive_message', {'message': f'Server echo: {msg}'}, broadcast=True)

# Background task to broadcast messages
def background_thread():
    count = 0
    while True:
        socketio.emit('receive_message', {'message': f'Automatic update #{count}'})
        count += 1
        socketio.sleep(5)

threading.Thread(target=background_thread, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)

