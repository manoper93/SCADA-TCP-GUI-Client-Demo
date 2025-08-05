import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import pygame
import os
import sys
import socket
import threading
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Check if an _internal folder exists (used in some build setups)
    internal_path = os.path.join(base_path, "_internal", relative_path)
    if os.path.exists(internal_path):
        return internal_path

    return os.path.join(base_path, relative_path)

class SCADASimulator:
    def __init__(self, root):
        pygame.mixer.init()
        self.root = root
        self.root.title("SCADA Simulator (Server)")
        self.root.geometry("400x800")
        
        # Initial system state
        self.emergency = False
        self.step = 0
        self.state = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve', 'emergency']}
        
        # Sockets
        self.client_socket = None
        self.server_socket = None

        self.load_resources()
        self.build_ui()
        self.update_ui()

        # Ask for IP/Port on the main thread BEFORE starting the server thread
        ip, port = self.ask_ip_port()
        
        # Start the server in a separate thread only if IP and port were provided
        if ip and port:
            server_thread = threading.Thread(target=self.start_server, args=(ip, port), daemon=True)
            server_thread.start()

    def ask_ip_port(self):
        """ Asks for the IP and port for the server to run on. This function must be called from the main thread. """
        ip = simpledialog.askstring("Server IP", "Enter server IP to run on:", initialvalue="127.0.0.1", parent=self.root)
        if not ip: return None, None # User canceled
        
        port = simpledialog.askinteger("Server Port", "Enter server port to run on:", initialvalue=5000, parent=self.root)
        if not port: return ip, None # User canceled

        return ip, port

    def start_server(self, ip, port):
        """ Sets up and starts the TCP server to listen for clients. """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allows reusing the address to avoid "Address already in use" errors
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((ip, port))
            self.server_socket.listen(1)
            self.update_status_label(f"Server listening on {ip}:{port}")
        except Exception as e:
            self.update_status_label(f"Error starting server: {e}")
            return

        # Infinite loop to accept new client connections
        while True:
            try:
                # Accept a new connection. This line is blocking.
                self.client_socket, client_address = self.server_socket.accept()
                self.update_status_label(f"Client connected from {client_address[0]}:{client_address[1]}")
                
                # Start a thread to handle the connected client
                receive_thread = threading.Thread(target=self.tcp_receive_loop, daemon=True)
                receive_thread.start()
                # Wait for the client thread to finish (when it disconnects)
                receive_thread.join() 
                self.update_status_label(f"Client disconnected. Waiting for new connection...")

            except Exception as e:
                self.update_status_label(f"Server loop error: {e}")
                break

    def update_status_label(self, text):
        """ Updates the status label text in the GUI. """
        # Use root.after to ensure the GUI update is done on the main thread
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.root.after(0, lambda: self.status_label.config(text=text))

    def load_resources(self):
        """ Loads images and sounds needed for the GUI. """
        R = {}
        try:
            path = resource_path('resources')
            R['led_on'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'led_on.png')))
            R['led_off'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'led_off.png')))
            R['valve_open'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'valve_open.png')))
            R['valve_closed'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'valve_closed.png')))
            R['tank'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'tank.png')))
            self.R = R
            self.sound_alarm = pygame.mixer.Sound(os.path.join(path, 'sound_alarm.mp3'))
            self.sound_valve = pygame.mixer.Sound(os.path.join(path, 'sound_valve.mp3'))
        except Exception as e:
            messagebox.showerror("Resource Error", f"Failed to load resources: {e}\nEnsure the 'resources' folder is in the same directory.")
            self.root.destroy()
            sys.exit(1)


    def build_ui(self):
        """ Builds the simulator's graphical user interface. """
        # Status Label
        self.status_label = tk.Label(self.root, text="Initializing...", fg="blue", font=("Helvetica", 10))
        self.status_label.pack(pady=5)

        tk.Label(self.root, image=self.R['tank']).pack(pady=10)

        frame_leds = tk.Frame(self.root)
        frame_leds.pack(pady=5)
        self.frames = {}

        for name in ['low_level', 'high_level']:
            subframe = tk.Frame(frame_leds)
            subframe.pack(side='left', padx=15)
            tk.Label(subframe, text=name.replace('_', ' ').title()).pack()
            lbl = tk.Label(subframe)
            lbl.pack()
            self.frames[name] = lbl

        frame_valves = tk.Frame(self.root)
        frame_valves.pack(pady=5)
        for name in ['in_valve', 'out_valve']:
            subframe = tk.Frame(frame_valves)
            subframe.pack(side='left', padx=15)
            tk.Label(subframe, text=name.replace('_', ' ').title()).pack()
            lbl = tk.Label(subframe)
            lbl.pack()
            self.frames[name] = lbl

        frame_emergency = tk.Frame(self.root)
        frame_emergency.pack(pady=5)
        tk.Label(frame_emergency, text="Emergency").pack()
        self.frames['emergency'] = tk.Label(frame_emergency)
        self.frames['emergency'].pack()

        tk.Button(self.root, text="▶ Next Step", command=self.next_step).pack(pady=10)
        tk.Button(self.root, text="⚠ Emergency", command=self.activate_emergency).pack()
        tk.Button(self.root, text="🔄 Reset", command=self.reset).pack(pady=10)

    def update_ui(self):
        """ Updates the GUI elements based on the current state. """
        st = self.state
        self.frames['low_level'].config(image=self.R['led_on'] if st['low_level'] else self.R['led_off'])
        self.frames['high_level'].config(image=self.R['led_on'] if st['high_level'] else self.R['led_off'])
        self.frames['in_valve'].config(image=self.R['valve_open'] if st['in_valve'] else self.R['valve_closed'])
        self.frames['out_valve'].config(image=self.R['valve_open'] if st['out_valve'] else self.R['valve_closed'])
        self.frames['emergency'].config(image=self.R['led_on'] if st['emergency'] else self.R['led_off'])
        self.root.update_idletasks()

    def next_step(self):
        """ Advances to the next simulation step (manually controlled). """
        if self.emergency:
            messagebox.showwarning("!", "Emergency activated! Please reset the system.")
            return
        st = {k: False for k in self.state}

        if self.step == 0:
            st['low_level'], st['in_valve'] = True, True
            self.sound_valve.play()
        elif self.step == 1:
            st['high_level'], st['out_valve'] = True, True
            self.sound_valve.play()
        else:
            self.step = -1
        self.state = st
        self.step += 1
        self.update_ui()

    def activate_emergency(self):
        """ Activates the emergency state. """
        self.emergency = True
        self.state = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve']}
        self.state['emergency'] = True
        self.sound_alarm.play()
        self.update_ui()

    def reset(self):
        """ Resets the system to the initial state. """
        self.emergency = False
        self.step = 0
        self.state = {k: False for k in self.state}
        self.update_ui()

    def tcp_receive_loop(self):
        """ Loop to receive data from the connected client. """
        while True:
            try:
                data = self.client_socket.recv(1024).decode().strip()
                if not data:
                    self.reset()
                    # Client disconnected
                    break
                
                # Use root.after to call the handler in the main GUI thread
                self.root.after(0, self.handle_message, data)

            except (ConnectionResetError, BrokenPipeError):
                # Common error when the client closes the connection abruptly
                break
            except Exception as e:
                print(f"TCP receive error: {e}")
                break
        
        # Close the client socket when the loop ends
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None


    def handle_message(self, msg):
        """ Processes the message received from the client and updates the state. """
        ack = "ACK_UNKNOWN"
        if msg == '0':
            # Simulates emptying the tank
            self.state['low_level'] = True
            self.state['high_level'] = False
            self.state['in_valve'] = True
            self.state['out_valve'] = False
            self.sound_valve.play()
            ack = "ACK_STATE_0_SET"
        elif msg == '1':
            # Simulates filling the tank
            self.state['low_level'] = False
            self.state['high_level'] = True
            self.state['in_valve'] = False
            self.state['out_valve'] = True
            self.sound_valve.play()
            ack = "ACK_STATE_1_SET"
        
        self.update_ui()
        
        # Send the confirmation (ACK) back to the client
        if self.client_socket:
            try:
                self.client_socket.sendall(ack.encode())
            except (BrokenPipeError, ConnectionResetError):
                # The client may have disconnected before receiving the ACK
                pass


if __name__ == '__main__':
    root = tk.Tk()
    app = SCADASimulator(root)
    root.mainloop()
