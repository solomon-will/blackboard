import tkinter as tk
from tkinter import colorchooser, simpledialog
import socket
import threading
import json

# --- 1. Networking & User Setup ---
root = tk.Tk()
root.geometry('800x600')
#gets username to display along with cursor on other screens
username = simpledialog.askstring("Username", "What is your name?") or "User"
root.title(f'Networking Project - {username}')

#initialize TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
try:
    #connect to the server IP and port number
    client_socket.connect(('172.20.10.2', 5555)) 
    connected = True
except:
    print("Running in offline mode.")

# --- 2. State & Variables ---
last_x, last_y = None, None #tracks mouse position for lines
current_color = "#FFFFFF"
erasing = False
remote_labels = {} #stores and update other users cursosrs

# --- 3. Networking Functions ---
def send_to_server(data_dict):
    #converts the dictionary to json and sends to ther the server
    if connected:
        try:
            message = json.dumps(data_dict) + '\n'
            client_socket.send(message.encode('utf-8'))
        except:
            pass

def receive_thread():
    #thread to listen for drawing data from other clients
    buffer = ""
    while True:
        try:
            chunk = client_socket.recv(4096).decode('utf-8')
            if not chunk: break
            buffer += chunk
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                data = json.loads(line)
                
                if data['type'] == 'draw':
                    #scales normalized coordinates to be consistent across all screens
                    w = canvas.winfo_width()
                    h = canvas.winfo_height()
                    canvas.create_line(
                        data['x1'] * w, data['y1'] * h,
                        data['x2'] * w, data['y2'] * h,
                        width=data['size'], fill=data['color'],
                        capstyle=tk.ROUND, smooth=True, tags="ink"
                    )
                elif data['type'] == 'move':
                    #update the text label representing a remote user
                    user, rx, ry = data['user'], data['x'], data['y']
                    if user not in remote_labels:
                        remote_labels[user] = canvas.create_text(rx, ry-10, text=user, fill="white")
                    else:
                        canvas.coords(remote_labels[user], rx, ry-10)
                        canvas.tag_raise(remote_labels[user])
                
                elif data['type'] == 'clear':
                    canvas.delete("ink")

                elif data['type'] == 'erase':
                    #erases items at remote coordinates
                    def erase_remote(d=data):
                        w = canvas.winfo_width()
                        h = canvas.winfo_height()
                        rx = d['x'] * w
                        ry = d['y'] * h
                        size = d['size']
                        items = canvas.find_overlapping(rx - size, ry - size, rx + size, ry + size)
                        for item in items:
                            if "ink" in canvas.gettags(item):
                                canvas.delete(item)
                    root.after(0, erase_remote)
        except:
            break

# --- 4. Drawing & UI Logic ---
def start_draw(event):
    #sets initial anchor point when mouse is first pressed
    global last_x, last_y
    last_x, last_y = event.x, event.y

def draw_on_canvas(event):
    #sends local drawing coordinates to the server
    global last_x, last_y
    x, y = event.x, event.y
    size = slider.get()
    
    if erasing:
        #eraser logic
        items = canvas.find_overlapping(x - size, y - size, x + size, y + size)
        for item in items:
            if "ink" in canvas.gettags(item):
                canvas.delete(item)
        send_to_server({'type': 'erase', 'x': x / canvas.winfo_width(), 'y': y / canvas.winfo_height(), 'size': size})
    else:
        #local drawing logic
        canvas.create_line(last_x, last_y, x, y, width=size, fill=current_color,
                           capstyle=tk.ROUND, smooth=True, tags="ink")
        send_to_server({
            'type': 'draw',
            'x1': last_x / canvas.winfo_width(),
            'y1': last_y / canvas.winfo_height(),
            'x2': x / canvas.winfo_width(),
            'y2': y / canvas.winfo_height(),
            'color': current_color,
            'size': size
        })
    
    last_x, last_y = x, y

def update_cursor(event):
    size = slider.get() + 2
    x, y = event.x, event.y
    #move the circle cursor and the user label
    canvas.coords(cursor_circle, x - size, y - size, x + size, y + size)
    canvas.coords(my_label, x, y - 10)
    
    canvas.tag_raise(cursor_circle)
    canvas.tag_raise(my_label)
    for label in remote_labels.values():
        canvas.tag_raise(label)
        
    send_to_server({'type': 'move', 'user': username, 'x': x, 'y': y})
    canvas.update_idletasks()

def toggle_eraser():
    #switch between drawing and eraser mode
    global erasing
    erasing = not erasing
    eraser_btn.config(text='Eraser ON' if erasing else 'Eraser', 
                      bg='red' if erasing else 'SystemButtonFace')

def set_color(new_color):
    #updates bush color
    global current_color, erasing
    current_color = new_color
    erasing = False
    color_preview.config(bg=new_color)

def pick_color():
    #opens color picker 
    color = colorchooser.askcolor(color=current_color)[1]
    if color: set_color(color)

def clear_board():
    #ckears canvas and clears it for remote users as well
    canvas.delete("ink") 
    send_to_server({'type': 'clear'})

# --- 5. Main Window & Layout ---


toolbar = tk.Frame(root)
toolbar.pack(fill=tk.X)

#presett color palette buttons
colors = ['#000000', '#ff0000', '#0000ff', '#00ff00', '#ffff00', '#ffffff']
for color in colors:
    lbl = tk.Label(toolbar, bg=color, width=3, relief='raised', cursor='hand2')
    lbl.bind('<Button-1>', lambda e, c=color: set_color(c))
    lbl.pack(side=tk.LEFT, padx=1)

slider = tk.Scale(toolbar, from_=1, to=50, orient=tk.HORIZONTAL, label='Brush Size')
slider.pack(side=tk.LEFT)

eraser_btn = tk.Button(toolbar, text='Eraser', command=toggle_eraser)
eraser_btn.pack(side=tk.LEFT)

tk.Button(toolbar, text='🎨 Pick Color', command=pick_color).pack(side=tk.LEFT)
color_preview = tk.Label(toolbar, bg=current_color, width=3, relief='solid')
color_preview.pack(side=tk.LEFT, padx=5)
tk.Button(toolbar, text='Clear All', command=clear_board).pack(side=tk.LEFT)

#main canvas setup
canvas = tk.Canvas(root, bg='#121111', highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

#local cursor visuals and username color
cursor_circle = canvas.create_oval(0, 0, 0, 0, outline='cyan')
my_label = canvas.create_text(0, 0, text=username, fill="#EB00FF")

#event bindings
canvas.bind('<ButtonPress-1>', start_draw)
canvas.bind('<B1-Motion>', lambda e: (draw_on_canvas(e), update_cursor(e)))
canvas.bind('<Motion>', update_cursor)
canvas.config(cursor="none")

#start network listener thread
if connected:
    threading.Thread(target=receive_thread, daemon=True).start()

root.mainloop()