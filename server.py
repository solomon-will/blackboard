import socket
import threading
import json

clients = [] #list of active client connections
draw_history = [] # list of all drawing events to send to new clients when they join
client_usernames = {} # maps client connections to their usernames for tracking who is who

# Broadcasts a message to all clients except the sender 
def broadcast(message, sender_conn):
    """Sends data to everyone except the person who sent it."""
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                clients.remove(client)

# Handles incoming messages from a client and broadcasts them to others
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    # When a new client connects, send them the entire drawing history so they can see what's already on the canvas
    for event in draw_history:
        conn.send(event)
    
    buffer = ""
    while True:
        try:
            chunk = conn.recv(4096).decode('utf-8')
            if not chunk:
                break
            buffer += chunk

            # Process complete lines of JSON data from the buffer
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line:
                    continue
                data = json.loads(line)
                raw = (line + '\n').encode('utf-8')
                
                if data.get('type') == 'join':
                    client_usernames[conn] = data['user']
                    broadcast(raw, conn)
                elif data.get('type') == 'draw':
                    draw_history.append(raw)
                elif data.get('type') == 'clear':
                    draw_history.clear()
                
                broadcast(raw, conn)
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    
    # When the client disconnects, remove them from the user list
    print(f"[DISCONNECT] {addr} disconnected.")
    if conn in client_usernames:
        leave_msg = (json.dumps({'type': 'leave', 'user': client_usernames[conn]}) + '\n').encode('utf-8')
        broadcast(leave_msg, conn)
        del client_usernames[conn]
    if conn in clients:
        clients.remove(conn)
    conn.close()

# Start the server and listen for incoming connections  
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5555)) 
server.listen()

#puts server into a loop waiting for new connections and starts a new thread to handle each one
print("[SERVER] Running and listening...")
while True:
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()