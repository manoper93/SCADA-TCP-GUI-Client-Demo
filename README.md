# 🔧 SCADA Simulator with Python Server & C++17 Client

A complete SCADA simulation project using a graphical Python interface as the **TCP server**, and a lightweight **C++ client** for sending control commands.

This project simulates a water tank system with valves, LEDs, emergency states, and step-by-step process visualization — ideal for embedded systems, automation, or industrial SCADA demonstrations.

---

## 🖥️ Features

- 🧠 **Python SCADA Server**
  - Tkinter GUI with tank, valves, LEDs, emergency indicators
  - Real-time control and visual feedback
  - Sound effects for emergency and valve actions

- 💬 **C++ TCP Client**
  - Command-line interface with retry logic
  - Sends tank fill/drain commands
  - Displays server acknowledgments

- 🔊 **Sound & Visual Effects**
  - Valve and emergency alarm sounds via `pygame`
  - Image indicators with `PIL.ImageTk`

- 🧪 **Step-by-Step Simulation**
  - Manual "Next Step" control
  - Emergency button and reset behavior
  - Communication via TCP/IP

---

## ⚙️ Requirements

### Python Server
- Python 3.x
- Libraries:
  - `tkinter` (usually included by default)
  - `Pillow` (`pip install pillow`)
  - `pygame` (`pip install pygame`)

### C++ Client (Windows)
- Windows OS with:
  - MinGW (`g++`)
- Uses:
  - `winsock2.h`, `ws2tcpip.h`, `windows.h`

---

## 🚀 Building the Executables

### 🐍 Python Server → `scada_simulator.exe`

Use **PyInstaller** to create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "resources;resources" scada_simulator.py
```

📁 Output: dist/scada_simulator.exe

### 🧱 C++ Client → `client.exe`

Use **g++** to create a standalone executable:

```bash
export PATH=$PATH:/c/MinGW/bin
g++ main.cpp -o client.exe -lws2_32 -std=c++17 -static-libgcc -static-libstdc++
```

📁 Output: client.exe

---

## 🌐 Communication Flow
1. Launch the server (scada_simulator.exe)
2. Choose the IP and port (e.g., 127.0.0.1:5000)
3. Server waits for TCP connection
4. Run the client (client.exe)
5. Enter IP and port (the same as server)
6. Send commands via the terminal
7. Visual SCADA GUI responds in real time (lights, sounds, status)

### 📡 Supported Commands (Client Side)
- 0         → Fill the tank (low-level LED ON, input valve OPEN)  
- 1         → Drain the tank (high-level LED ON, output valve OPEN)    
- exit      → Disconnect client and set RESET on Server Side

## 🔄 Possible Extensions
- Real-time sensor simulation or plotting
- Modbus or MQTT communication
- Data logging with SQLite or CSV
- GUI-based C++ client
- Multiple client handling

## 🙏 Credits
Developed as an educational project to demonstrate:
- Basic SCADA functionality
- Real-time control logic
- Cross-language communication between Python and C++

---

## 📽️ Vídeo

<div align="center">

https://github.com/user-attachments/assets/1d0a640f-fc8a-449d-b3e8-b8bba26f79f3

</div>
