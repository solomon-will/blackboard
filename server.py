import socket
import threading
import json

clients = [] #list of active socket connections
draw_history = [] #list of drawing events for new users

def broadcast(message, sender_conn):
    #sends message to all clients except the one who sent it
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                clients.remove(client)

def handle_client(conn, addr):
    #individual thread for each user to process incoming data
    print(f"[NEW CONNECTION] {addr} connected.")
    
    #sends every existing drawing history to the new user
    for event in draw_history:
        conn.send(event)
    
    buffer = ""
    while True:
        try:
            chunk = conn.recv(4096).decode('utf-8')
            if not chunk:
                break
            buffer += chunk
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line:
                    continue
                data = json.loads(line)
                raw = (line + '\n').encode('utf-8')
                
                #saves drawing actions for users that join after
                if data.get('type') == 'draw':
                    draw_history.append(raw)
                elif data.get('type') == 'clear':
                    draw_history.clear()
                
                #shares action with everyone
                broadcast(raw, conn)
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    
    
    print(f"[DISCONNECT] {addr} disconnected.")
    if conn in clients:
        clients.remove(conn)
    conn.close()

#server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5555)) 
server.listen()

print("[SERVER] Running and listening...")
while True:
    #loops and accepts new incoming connections and starts a dedicated thread
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()