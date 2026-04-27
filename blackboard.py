import tkinter as tk
from tkinter import colorchooser, simpledialog
import socket
import threading
import json

# --- 1. Networking & User Setup ---
username = simpledialog.askstring("Username", "What is your name?") or "User"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
try:
    client_socket.connect(('10.5.3.90', 5555)) 
    connected = True
except:
    print("Running in offline mode.")

# --- 2. State & Variables ---
last_x, last_y = None, None
current_color = "#FFFFFF"
erasing = False
remote_labels = {} 

# --- 3. Networking Functions ---
def send_to_server(data_dict):
    if connected:
        try:
            message = json.dumps(data_dict) + '\n'
            client_socket.send(message.encode('utf-8'))
        except:
            pass

def receive_thread():
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
                    # Added tags="ink" here so remote drawings can be erased too
                    canvas.create_line(data['x1'], data['y1'], data['x2'], data['y2'], 
                                       width=data['size'], fill=data['color'], 
                                       capstyle=tk.ROUND, smooth=True, tags="ink")
                
                elif data['type'] == 'move':
                    user, rx, ry = data['user'], data['x'], data['y']
                    if user not in remote_labels:
                        remote_labels[user] = canvas.create_text(rx, ry-15, text=user, fill="white")
                    else:
                        canvas.coords(remote_labels[user], rx, ry-15)
                        canvas.tag_raise(remote_labels[user])
                
                elif data['type'] == 'clear':
                    # Only delete "ink", keeps labels and cursors safe
                    canvas.delete("ink") 
        except:
            break

# --- 4. Drawing & UI Logic ---
def start_draw(event):
    global last_x, last_y
    last_x, last_y = event.x, event.y

def draw_on_canvas(event):
    global last_x, last_y
    x, y = event.x, event.y
    size = slider.get()
    
    if erasing:
        # Find everything in the eraser area
        items = canvas.find_overlapping(x - size, y - size, x + size, y + size)
        for item in items:
            # CHECK THE TAG: Only delete if it's "ink"
            if "ink" in canvas.gettags(item):
                canvas.delete(item)
        # Optional: Broadcast eraser movement if you want others to see things disappear
        # send_to_server({'type': 'erase', 'x': x, 'y': y, 'size': size})
    else:
        # Added tags="ink" here
        canvas.create_line(last_x, last_y, x, y, width=size, fill=current_color, 
                           capstyle=tk.ROUND, smooth=True, tags="ink")
        send_to_server({'type': 'draw', 'x1': last_x, 'y1': last_y, 'x2': x, 'y2': y, 
                        'color': current_color, 'size': size})
    
    last_x, last_y = x, y

def update_cursor(event):
    size = slider.get() + 2
    x, y = event.x, event.y
    canvas.coords(cursor_circle, x - size, y - size, x + size, y + size)
    canvas.coords(my_label, x, y - 15)
    
    # Ensure the UI stays ON TOP of the drawings
    canvas.tag_raise(cursor_circle)
    canvas.tag_raise(my_label)
    for label in remote_labels.values():
        canvas.tag_raise(label)
        
    send_to_server({'type': 'move', 'user': username, 'x': x, 'y': y})
    canvas.update_idletasks()

def toggle_eraser():
    global erasing
    erasing = not erasing
    eraser_btn.config(text='Eraser ON' if erasing else 'Eraser', 
                      bg='red' if erasing else 'SystemButtonFace')

def set_color(new_color):
    global current_color, erasing
    current_color = new_color
    erasing = False
    color_preview.config(bg=new_color)

def pick_color():
    color = colorchooser.askcolor(color=current_color)[1]
    if color: set_color(color)

def clear_board():
    canvas.delete("ink") # Only clear the drawings
    send_to_server({'type': 'clear'})

# --- 5. Main Window & Layout ---
root = tk.Tk()
root.geometry('800x600')
root.title(f'Networking Project - {username}')

toolbar = tk.Frame(root)
toolbar.pack(fill=tk.X)

colors = ['#000000', '#ff0000', '#0000ff', '#00ff00', '#ffff00', '#ffffff']
for color in colors:
    tk.Button(toolbar, bg=color, width=2, command=lambda c=color: set_color(c)).pack(side=tk.LEFT)

slider = tk.Scale(toolbar, from_=1, to=50, orient=tk.HORIZONTAL, label='Brush Size')
slider.pack(side=tk.LEFT)

eraser_btn = tk.Button(toolbar, text='Eraser', command=toggle_eraser)
eraser_btn.pack(side=tk.LEFT)

tk.Button(toolbar, text='🎨 Pick Color', command=pick_color).pack(side=tk.LEFT)
color_preview = tk.Label(toolbar, bg=current_color, width=3, relief='solid')
color_preview.pack(side=tk.LEFT, padx=5)
tk.Button(toolbar, text='Clear All', command=clear_board).pack(side=tk.LEFT)

canvas = tk.Canvas(root, bg='#121111', highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

# These do NOT have the "ink" tag, so they won't be erased
cursor_circle = canvas.create_oval(0, 0, 0, 0, outline='cyan')
my_label = canvas.create_text(0, 0, text=username, fill="yellow")

canvas.bind('<ButtonPress-1>', start_draw)
canvas.bind('<B1-Motion>', lambda e: (draw_on_canvas(e), update_cursor(e)))
canvas.bind('<Motion>', update_cursor)
canvas.config(cursor="none")

if connected:
    threading.Thread(target=receive_thread, daemon=True).start()

root.mainloop()