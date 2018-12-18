from src.Views import LoginView, MainView, Message
from src.Models import User
from threading import Thread
from hashlib import sha256
from queue import Queue
import src.server_host as server_host
from socket import socket, AF_INET, SOCK_STREAM
import json
from tkinter import Tk, BooleanVar, messagebox, END


class GenericController:
    def __init__(self, app: Tk, sock: socket = None, model: User = None, view = None):
        self.app = app
        self.model = model
        self.view = view
        self.socket = sock

    def connect(self):
        pass

    def send_request(self, request: dict):
        raise NotImplementedError('method send_request must be implemented')

    def receive_response(self):
        raise NotImplementedError('method receive_response must be implemented')


class LoginViewController(GenericController):
    def __init__(self, app: Tk, sock: socket = None, model: User = None, view: LoginView = None):
        super().__init__(app, sock, model, view)
        self.model = model if model is not None else User()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.sha256 = sha256()
        self.user_logged_state = BooleanVar(app)
        self.user_logged_state.trace('w', self.user_state_changed)

    def connect(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect(server_host.host)

    def send_request(self, request: dict):
        serialized_request = json.dumps(request)
        self.socket.sendall(serialized_request.encode())

    def receive_response(self):
        data = bytes()
        while True:
            received = self.socket.recv(4096)
            if not received:
                break
            elif len(received) < 4096:
                data += received
                break
            else:
                data += received

        response = json.loads(data.decode())
        return response

    def hash_password(self, raw_password: str):
        self.sha256.update(raw_password.encode())
        return self.sha256.hexdigest()

    def username_var_changed(self, *args):
        username = self.view.username.get()
        password = self.view.password.get()

        # Unlock the password entry only if there's something in the username entry
        if username != '':
            self.view.pass_entry['state'] = 'normal'
            # Unlock the submit button only if both the username and password typed are at least 8 chars long
            self.view.submit_button['state'] = 'normal' if len(username) >= 8 and len(password) >= 8 else 'disabled'
        else:
            self.view.pass_entry['state'] = 'disabled'
            self.view.submit_button['state'] = 'disabled'

    def password_var_changed(self, *args):
        username = self.view.username.get()
        password = self.view.password.get()

        # Unlock the submit button only if both the username and password typed are at least 8 chars long
        if password != '':
            self.view.submit_button['state'] = 'normal' if len(username) >= 8 and len(password) >= 8 else 'disabled'
        else:
            self.view.submit_button['state'] = 'disabled'

    def submit(self, *args):
        username = self.view.username.get()
        self.model.username = username
        hashed_password = self.hash_password(self.view.password.get())
        self.model.password = hashed_password

        self.connect()
        request = {
            'request': self.view.action.get(),
            'user': {'username': self.model.username, 'password': self.model.password}
        }
        # print(request)
        self.send_request(request)
        response = self.receive_response()

        if response['info'] == 'Logged':
            self.user_logged_state.set(True)
        else:
            messagebox.showwarning(response['info'], title='')

    def start_chat_view(self):
        chat_view = MainView(self.app, self.model)
        chat_controller = MainViewController(chat_view, self.model)
        chat_view.controller = chat_controller

    def user_state_changed(self, *args):
        if self.user_logged_state.get() is True:
            for widget in self.app.slaves():
                widget.destroy()


class MainViewController(GenericController):
    def __init__(self, app: Tk, sock: socket, view: MainView, model: User):
        super().__init__(app, sock, model, view)
        # self.model = model
        # self.view = view
        # self.socket = sock
        self.received_responses = Queue()
        self.response_handler = Thread(target=self.treat_responses, daemon=True)
        self.response_handler.start()
        self.received_messages = Queue()
        self.received_messages_handler = Thread(target=self.receive_messages, daemon=True)
        self.received_messages_handler.start()

    def send_request(self, request: dict):
        serialized_request = json.dumps(request)
        self.socket.sendall(serialized_request.encode())

    def receive_response(self):
        while True:
            data = bytes()
            while True:
                received = self.socket.recv(4096)
                if not received:
                    break
                # elif len(received) < 4096:
                #     data += received
                #     break
                else:
                    data += received

            self.received_responses.put(data)

    def treat_responses(self):
        while True:
            while self.received_responses.empty() is False:
                response = json.loads(self.received_responses.get())

                if 'message' in response:
                    self.received_messages.put(response['message'])
                elif 'info' in response:
                    messagebox.showinfo('Server response', response['info'])

    def receive_messages(self):
        while True:
            while self.received_messages.empty() is False:
                # json_message = {
                #     'message': {
                #         'sender': 'username'
                #         'content': 'message content'
                #     }
                # }
                json_message = self.received_messages.get()

                if json_message['sender'] == self.model.username:
                    json_message['sender'] = 'Você'

                message = '{}: {}'.format(json_message['sender'], json_message['content'])
                self.view.active_chat.insert(END, message)

    def search_username_changed(self, *args):
        username = self.view.search_username.get()

        if len(username) >= 8:
            self.view.search_button['state'] = 'normal'
        else:
            self.view.search_button['state'] = 'disabled'

    def search_user(self, *args):
        username = self.view.search_username.get()

        request = {
            'request': 'prefetch_messages',
            'with': username
        }

    def message_changed(self, *args):
        pass

    def send_message(self, *args):
        pass


# if __name__ == '__main__':
#     p = 'testPass123'
#     hasher = sha256(p.encode())
#     print(hasher.hexdigest())
#     print('cb92d111bf8d6bcf59e905d5fc50d5d403f0a59bf9a857b711020ba083b524a9')
