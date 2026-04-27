import socket
import threading

clients = []

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
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            broadcast(data, conn)
        except:
            break
    
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