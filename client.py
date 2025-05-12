import socket
import pickle
import struct
import cv2
import numpy as np
import threading
import tkinter as tk

SERVER_IP = ""  # <- put your server IP
PASSWORD = "mypassword" # <- change this to your password
disconnect_flag = False
client_socket = None
root = None

def disconnect():
    global disconnect_flag
    disconnect_flag = True
    print("Disconnect button pressed.")

def create_disconnect_button():
    global root
    root = tk.Tk()
    root.title("Controls")
    root.geometry("200x100")
    disconnect_btn = tk.Button(root, text="Disconnect", command=disconnect, height=2, width=15)
    disconnect_btn.pack(pady=20)
    root.mainloop()

def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        try:
            window_width = 1365
            window_height = 768
            client_socket.send(f"MOVE {x} {y} {window_width} {window_height}".encode())
        except:
            pass
    elif event == cv2.EVENT_LBUTTONDOWN:
        try:
            client_socket.send("CLICK LEFT".encode())
        except:
            pass
    elif event == cv2.EVENT_RBUTTONDOWN:
        try:
            client_socket.send("CLICK RIGHT".encode())
        except:
            pass

def connect_to_server():
    global disconnect_flag, client_socket, root

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, 9999))
    except Exception as e:
        print("Connection failed:", e)
        if root:
            root.quit()
        return

    client_socket.send(PASSWORD.encode())
    auth_response = client_socket.recv(1024).decode()
    if auth_response != "AUTH_SUCCESS":
        print("Authentication failed!")
        if root:
            root.quit()
        return
    print("Connected and authenticated!")

    data = b""
    payload_size = struct.calcsize("Q")

    cv2.namedWindow("Remote Screen")
    cv2.setMouseCallback("Remote Screen", mouse_event)

    while not disconnect_flag:
        while len(data) < payload_size:
            packet = client_socket.recv(4096)
            if not packet:
                return
            data += packet
        packed_msg_size = data[:payload_size]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        data = data[payload_size:]

        while len(data) < msg_size:
            data += client_socket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        frame = np.array(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        window_width = 1365
        window_height = 768
        frame = cv2.resize(frame, (window_width, window_height))
        cv2.imshow("Remote Screen", frame)
        if cv2.waitKey(1) == ord('q'):
            break
    try:
        client_socket.send("DISCONNECT".encode())
    except:
        pass
    client_socket.close()
    cv2.destroyAllWindows()
    if root:
        root.quit()
    print("Disconnected successfully.")

if __name__ == "__main__":
    control_thread = threading.Thread(target=create_disconnect_button)
    control_thread.start()
    connect_to_server()