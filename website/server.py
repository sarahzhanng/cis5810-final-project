from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from pymongo import MongoClient
from flask_socketio import SocketIO
import time
import threading
import requests
import base64

import cv2
import numpy as np
from tryon import TryOnServer
import torch

app = Flask(__name__)
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["cis-5810"]
users_collection = db["users"]
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

socketio = SocketIO(app, cors_allowed_origins="*")

tryon = TryOnServer(device="cuda" if torch.cuda.is_available() else "cpu")


@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.json

    existing_user = users_collection.find_one({'username': data['username']})
    if existing_user:
        return jsonify({"message": "Username already exists"}), 409
    
    users_collection.insert_one({
        'username': data['username'],
        'password': data['password'],
        'saved': []
    })
    return jsonify({'message': 'Signup Successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users_collection.find_one({'username': data['username']})
    print(user)
    if (user is None) or (len(user) == 0) or (user['password'] != data['password']):
        print('error') 
        return jsonify({"message": "Incorrect username or password"}), 401
        
    resp = make_response(jsonify({'message': 'Login Successful', 'token': data['username']}), 201)
    resp.set_cookie(
        "token",
        data['username'],
        httponly=True,
        samesite="None",
        secure=True
    )
    return resp

@app.route('/logout')
def logout():
    resp = make_response(jsonify({"message": "Logout successful"}), 200)
    resp.delete_cookie(
        "token",
        path="/",
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

@app.route('/save_cloth', methods=['POST'])
def save_cloth():
    data = request.json
    
    username = data['username']
    cloth = data['cloth']
    uploaded = data['uploaded']

    users_collection.update_many(
        {'username': username},
        {'$addToSet': {'saved': {'cloth': cloth, 'uploaded': uploaded}}}
    )

    return jsonify({'message': 'Cloth saved'}), 201

@app.route('/remove_cloth', methods=['DELETE'])
def remove_cloth():
    data = request.json
    username = data['username']
    cloth = data['cloth']

    users_collection.update_one(
        {'username': username},
        {'$pull': {'saved': {'cloth': cloth}}}
    )

    return jsonify({'message': 'Cloth removed'}), 201

@app.route('/get_saved_cloth/<username>')
def get_saved_cloth(username):
    user_doc = users_collection.find_one(
        {'username': username},
        {'_id': 0, 'saved': 1, 'username': 1}
    )
    
    if not user_doc:
        return jsonify({'uploaded': [], 'base64': []}), 200

    uploaded = [img['cloth'] for img in user_doc['saved'] if img.get('uploaded') == 'T']
    base64 = [img['cloth'] for img in user_doc['saved'] if img.get('uploaded') == 'F']

    return jsonify({'uploaded': uploaded, 'static': base64}), 201


# SocketIO event
clients = {}

@socketio.on('send_message')
def handle_message(img, cloth):
    sid = request.sid

    if img.startswith("data:"):
        img = img.split(",")[1]
    img_bytes = base64.b64decode(img)
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    clotharr = np.frombuffer(cloth, np.uint8)
    cloth_cv = cv2.imdecode(clotharr, cv2.IMREAD_UNCHANGED)

    # one-time loop of RealtimeTryOn
    output = tryon.run(frame_cv, cloth_cv)

    _, buffer = cv2.imencode('.png', output)
    socketio.emit('receive_update', buffer.tobytes())

    if sid not in clients or not clients[sid]['running']:
        print('here?')
        clients[sid] = {'running': True}
        # Use socketio.start_background_task instead of threading.Thread for compatibility
        t = socketio.start_background_task(background_thread, sid)
        clients[sid]['thread'] = t


@socketio.on("stop_thread")
def stop_thread():
    sid = request.sid
    if sid in clients:
        print(sid, 'stopping background task')
        clients[sid]['running'] = False
        socketio.emit('receive_message', {'message': 'Stopped'}, to=sid)

# Background task to broadcast messages
def background_thread(sid):
    count = 0
    while sid in clients and clients[sid]['running']:
        print('background thread loop start')
        socketio.emit('reminder', to=sid)
        count += 1
        socketio.sleep(5)

    print('terminating background task')

# threading.Thread(target=background_thread, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)

