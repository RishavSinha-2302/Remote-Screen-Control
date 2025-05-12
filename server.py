import socket
import threading
import pickle
import struct
import pyautogui

PASSWORD = "mypassword" # Change this to your password

def handle_client(client_socket):
    try:
        auth = client_socket.recv(1024).decode()
        if auth != PASSWORD:
            client_socket.send("AUTH_FAIL".encode())
            client_socket.close()
            return
        client_socket.send("AUTH_SUCCESS".encode())
        while True:
            try:
                # Check if client sent mouse control command
                client_socket.settimeout(0.1)  # Non-blocking small timeout
                try:
                    command_undecoded = client_socket.recv(1024)
                    try:
                        command = command_undecoded.decode()
                        if command.startswith("MOVE"):
                            parts = command.split()
                            x, y, window_w, window_h = map(int, parts[1:])

                            # Get server screen size
                            screen_w, screen_h = pyautogui.size()

                            # Scale coordinates
                            real_x = int(x * screen_w / window_w)
                            real_y = int(y * screen_h / window_h)

                            pyautogui.moveTo(real_x, real_y)
                        elif command == "CLICK LEFT":
                            pyautogui.click(button='left')
                        elif command == "CLICK RIGHT":
                            pyautogui.click(button='right')
                        elif command == "DISCONNECT":
                            print("Client requested disconnection.")
                            client_socket.close()
                            break
                    except (ValueError, UnicodeDecodeError):
                        pass
                except socket.timeout:
                    pass

                # Reset timeout for sending screen
                client_socket.settimeout(None)

                # Send screen
                screenshot = pyautogui.screenshot()
                data = pickle.dumps(screenshot)
                message = struct.pack("Q", len(data)) + data
                client_socket.sendall(message)
            except Exception as e:
                if type(e).__name__ == "ConnectionResetError":
                    print("Client requested disconnection.")
                    break
                print("Connection lost:", e)
                client_socket.close()
                break
    except Exception as e:
        print("Error handling client:", e)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("Listening for connections...")

    while True:
        client_socket, addr = server.accept()
        print("Connection from:", addr)
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()