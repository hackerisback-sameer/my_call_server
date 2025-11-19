from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_123'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected users
connected_users = {}

@app.route('/')
def home():
    return "🚀 My Call Server is Running on Railway!"

@app.route('/status')
def status():
    return jsonify({
        'status': 'online', 
        'users_online': len(connected_users),
        'users': list(connected_users.keys())
    })

@socketio.on('connect')
def handle_connect():
    print(f"🔗 Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    for user_id, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[user_id]
            print(f"🚪 User disconnected: {user_id}")
            socketio.emit('user_left', {'user_id': user_id}, broadcast=True)
            break

@socketio.on('register')
def handle_register(data):
    user_id = data.get('user_id')
    if user_id:
        connected_users[user_id] = request.sid
        print(f"✅ User registered: {user_id}")
        socketio.emit('user_list', {'users': list(connected_users.keys())}, broadcast=True)

@socketio.on('call_request')
def handle_call_request(data):
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    
    print(f"📞 Call: {from_user} → {to_user}")
    
    if to_user in connected_users:
        socketio.emit('incoming_call', {
            'from_user': from_user
        }, room=connected_users[to_user])
    else:
        socketio.emit('call_status', {'status': 'user_offline'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    print(f"🚀 Starting server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False)
