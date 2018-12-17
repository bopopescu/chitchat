import src.server_host as server_host
import socket
import json
from src.Views import LoginView, MainView
from src.Models import User
from threading import Thread
from hashlib import sha256
from queue import Queue


class GenericController:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect(server_host.host)

    def send_request(self, request: dict):
        raise NotImplementedError('method send_request must be implemented')

    def receive_response(self):
        raise NotImplementedError('method receive_response must be implemented')


class LoginViewController(GenericController):
    def __init__(self, model: User = None, view: LoginView = None):
        super().__init__()
        self.model = User() if User is not None else model
        self.view = LoginView(self, self.model) if view is not None else view
        self.sha256 = sha256()
        self.action = ''
        self.result = ''

    def send_request(self, request: dict):
        self.socket.sendall(json.dumps(request).encode())

    def receive_response(self):
        data = bytes()
        while True:
            received = self.socket.recv(4096)
            if received is None:
                break
            elif len(received) < 4096:
                data += received
                break
            else:
                data += received

        return json.loads(data.decode())

    def hash_password(self, raw_password: str):
        self.sha256.update(raw_password.encode())
        return self.sha256.hexdigest()

    def set_action(self, user_input: str):
        self.action = user_input

    def set_username(self, user_input: str):
        if len(user_input) < 8:
            self.result = ' Username must be at least 8 chars long '
            self.view.show_result()
        else:
            self.result = 'valid username'
            self.model.username = user_input

    def set_password(self, user_input: str):
        if len(user_input) < 8:
            self.result = ' Password must be at least 8 chars long '
            self.view.show_result()
            return

        hashed_password = self.hash_password(user_input)
        self.model.password = hashed_password

        if self.action == 1 or self.action == 2:
            self.connect()
            self.result = self.login() if self.action == 1 else self.register()
            self.view.show_result()

            if self.model.logged:
                self.start_chat_view()
        else:
            self.result = ' Invalid choice '
            self.view.show_result()

        self.result = ''

    def login(self):
        request = {
            'request': 'login',
            'user': {
                'username': self.model.username,
                'password': self.model.password
            }
        }
        self.send_request(request)
        response = self.receive_response()

        if response['message'] == 'Logged':
            self.model.logged = True
            result = ' Logged '
        else:
            result = ' Invalid username or password '

        return result

    def register(self):
        request = {
            'request': 'register',
            'user': {
                'username': self.model.username,
                'password': self.model.password
            }
        }
        self.send_request(request)
        response = self.receive_response()

        if response['message'] == 'Logged':
            self.model.logged = True
            result = ' Welcome '
        else:
            result = ' User already exists '

        return result

    def start_chat_view(self):
        chat_view = MainView(self.model)
        chat_controller = MainViewController(chat_view, self.model)
        chat_view.controller = chat_controller
        chat_view.run()


class MainViewController:
    def __init__(self, view: MainView, model: User):
        self.model = model
        self.view = view
        self.received_messages = Queue()

