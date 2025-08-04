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
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    internal_path = os.path.join(base_path, "_internal", relative_path)
    if os.path.exists(internal_path):
        return internal_path

    return os.path.join(base_path, relative_path)

class SCADASimulator:
    def __init__(self, root):
        pygame.mixer.init()
        self.root = root
        self.root.title("SCADA Simulator")
        self.root.geometry("400x800")
        self.emergency = False
        self.step = 0
        self.state = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve', 'emergency']}

        self.load_resources()
        self.build_ui()
        self.update_ui()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip, self.port = self.ask_ip_port()
        threading.Thread(target=self.try_connect, daemon=True).start()

    def ask_ip_port(self):
        ip = simpledialog.askstring("IP Address", "Enter server IP:", initialvalue="127.0.0.1")
        port = simpledialog.askinteger("Port", "Enter server port:", initialvalue=5000)
        if not ip or not port:
            messagebox.showerror("Error", "IP and Port are required.")
            self.root.destroy()
            sys.exit(1)
        return ip, port

    def try_connect(self):
        while True:
            try:
                self.update_status_label(f"Connecting to {self.ip}:{self.port}...")
                self.sock.connect((self.ip, self.port))
                self.update_status_label(f"Connected to {self.ip}:{self.port}")
                threading.Thread(target=self.tcp_receive_loop, daemon=True).start()
                break
            except Exception as e:
                self.update_status_label(f"No connection. Retrying...")
                time.sleep(2)

    def update_status_label(self, text):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=text)
        else:
            self.status_label = tk.Label(self.root, text=text, fg="blue")
            self.status_label.pack(pady=5)

    def load_resources(self):
        R = {}
        path = resource_path('resources')
        R['led_on'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'led_on.png')))
        R['led_off'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'led_off.png')))
        R['valve_open'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'valve_open.png')))
        R['valve_closed'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'valve_closed.png')))
        R['tank'] = ImageTk.PhotoImage(Image.open(os.path.join(path, 'tank.png')))
        self.R = R
        self.sound_alarm = pygame.mixer.Sound(os.path.join(path, 'sound_alarm.wav'))
        self.sound_valve = pygame.mixer.Sound(os.path.join(path, 'sound_valve.wav'))

    def build_ui(self):
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
        st = self.state
        self.frames['low_level'].config(image=self.R['led_on'] if st['low_level'] else self.R['led_off'])
        self.frames['high_level'].config(image=self.R['led_on'] if st['high_level'] else self.R['led_off'])
        self.frames['in_valve'].config(image=self.R['valve_open'] if st['in_valve'] else self.R['valve_closed'])
        self.frames['out_valve'].config(image=self.R['valve_open'] if st['out_valve'] else self.R['valve_closed'])
        self.frames['emergency'].config(image=self.R['led_on'] if st['emergency'] else self.R['led_off'])

    def next_step(self):
        if self.emergency:
            messagebox.showwarning("!", "Emergency activated! Please reset the system.")
            return
        st = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve', 'emergency']}
        if self.step == 0:
            st['low_level'], st['in_valve'] = True, True
            self.sound_valve.play()
        elif self.step == 1:
            st['low_level'], st['in_valve'] = True, True
        elif self.step == 2:
            st['high_level'] = True
        elif self.step == 3:
            st['high_level'], st['out_valve'] = True, True
            self.sound_valve.play()
        elif self.step == 4:
            st['low_level'] = True
        else:
            self.step = -1
        self.state = st
        self.step += 1
        self.update_ui()

    def activate_emergency(self):
        self.emergency = True
        self.state = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve']}
        self.state['emergency'] = True
        self.sound_alarm.play()
        self.update_ui()

    def reset(self):
        self.emergency = False
        self.step = 0
        self.state = {k: False for k in ['low_level', 'high_level', 'in_valve', 'out_valve', 'emergency']}
        self.update_ui()

    def tcp_receive_loop(self):
        while True:
            try:
                data = self.sock.recv(1024).decode().strip()
                if not data:
                    break
                print("Received:", data)
                self.handle_message(data)
            except Exception as e:
                print("TCP receive error:", e)
                self.update_status_label("Connection lost. Reconnecting...")
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.try_connect()
                break

    def handle_message(self, msg):
        if msg == '0':
            self.state['low_level'] = False
            self.state['in_valve'] = False
            ack = "ACK_LOW"
        elif msg == '1':
            self.state['low_level'] = True
            self.state['in_valve'] = True
            ack = "ACK_HIGH"
        else:
            ack = "ACK_UNKNOWN"

        self.update_ui()
        try:
            self.sock.sendall(ack.encode())
        except:
            pass

if __name__ == '__main__':
    root = tk.Tk()
    app = SCADASimulator(root)
    root.mainloop()
