import requests
import json
import threading
import time
from websocket import create_connection
import subprocess
import sys

class SimpleCallClient:
    def __init__(self, server_url, user_id):
        # Convert HTTP to WebSocket
        ws_url = server_url.replace('https', 'wss').replace('http', 'ws') + '/socket.io/?transport=websocket'
        self.server_url = server_url
        self.ws_url = ws_url
        self.user_id = user_id
        self.ws = None
        self.running = True
        
    def connect(self):
        try:
            print(f"🔗 Connecting to {self.server_url}...")
            
            # First test HTTP connection
            try:
                response = requests.get(f"{self.server_url}/status", timeout=10)
                print("✅ Server is online")
            except:
                print("❌ Server is not responding")
                return
            
            # Try WebSocket connection
            self.ws = create_connection(self.ws_url, timeout=10)
            
            # Register user
            register_msg = '42["register", {"user_id": "' + self.user_id + '"}]'
            self.ws.send(register_msg)
            print(f"✅ Registered as: {self.user_id}")
            
            # Start listening for messages
            self.listen_thread = threading.Thread(target=self.listen_messages)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("💡 Tip: Server might still be starting up. Wait 2 minutes and try again.")
    
    def listen_messages(self):
        while self.running:
            try:
                message = self.ws.recv()
                if message.startswith('42'):
                    data = json.loads(message[2:])
                    self.handle_message(data)
                elif message.startswith('40'):
                    print("✅ Connected to server")
                elif message == '2':
                    self.ws.send('3')  # Ping response
            except Exception as e:
                if self.running:
                    print(f"📡 Connection lost: {e}")
                break
    
    def handle_message(self, data):
        event = data[0]
        payload = data[1] if len(data) > 1 else {}
        
        if event == 'incoming_call':
            print(f"📞 INCOMING CALL from: {payload['from_user']}")
            try:
                subprocess.run(['termux-notify', '-t', 'Incoming Call', '-c', f'From: {payload["from_user"]}'])
                subprocess.run(['termux-vibrate', '-d', '1000'])
            except:
                print("💡 Enable termux-api for notifications")
                
        elif event == 'user_list':
            users = payload.get('users', [])
            other_users = [u for u in users if u != self.user_id]
            if other_users:
                print(f"👥 Users online: {', '.join(other_users)}")
            else:
                print("👥 No other users online")
                
        elif event == 'user_left':
            print(f"🚪 User left: {payload['user_id']}")
    
    def make_call(self, target_user):
        call_msg = f'42["call_request", {{"from_user": "{self.user_id}", "to_user": "{target_user}"}}]'
        self.ws.send(call_msg)
        print(f"📞 Calling {target_user}...")
    
    def disconnect(self):
        self.running = False
        if self.ws:
            self.ws.close()

def main():
    SERVER_URL = "https://desirable-quietude.railway.app"
    
    print("🌐 Free Call Server - Termux")
    print(f"Server: {SERVER_URL}")
    user_id = input("Enter your username: ")
    
    client = SimpleCallClient(SERVER_URL, user_id)
    client.connect()
    
    try:
        while True:
            print("\nOptions:")
            print("1. Call user")
            print("2. Check online users") 
            print("3. Exit")
            choice = input("Choose (1/2/3): ")
            
            if choice == '1':
                target = input("Enter username to call: ")
                client.make_call(target)
            elif choice == '2':
                # Re-register to get updated user list
                client.ws.send('42["register", {"user_id": "' + user_id + '"}]')
            elif choice == '3':
                break
            time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
