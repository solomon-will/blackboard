import socket
import threading
import json

clients = []
draw_history = []

def broadcast(message, sender_conn):
    """Sends data to everyone except the person who sent it."""
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                clients.remove(client)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    # send existing drawings to the new client
    for event in draw_history:
        conn.send(event)
    
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            
            msg = json.loads(data.decode('utf-8').strip())
            
            if msg.get('type') == 'draw':
                draw_history.append(data)
            elif msg.get('type') == 'clear':
                draw_history.clear()
            
            broadcast(data, conn)
        except:
            break
    
    print(f"[DISCONNECT] {addr} disconnected.")
    clients.remove(conn)
    conn.close()
    
    print(f"[DISCONNECT] {addr} disconnected.")
    clients.remove(conn)
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# '0.0.0.0' allows connections from other machines on the network
server.bind(('0.0.0.0', 5555)) 
server.listen()

print("[SERVER] Running and listening...")
while True:
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()