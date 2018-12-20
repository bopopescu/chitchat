import time

from Views import LoginView, MainView, Message
from Models import User
from datetime import datetime
from threading import Thread
from hashlib import sha256
from queue import Queue
from socket import socket, AF_INET, SOCK_STREAM
from tkinter import Tk, BooleanVar, messagebox, END
import server_host as server_host
import json


class GenericController:
    def __init__(self, app: Tk, sock: socket, model: User = None, view = None):
        self.app = app
        self.socket = sock
        self.model = model
        self.view = view

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
            messagebox.showwarning('Server says', response['info'])

    def start_main_view(self):
        controller = MainViewController(self.app, self.socket, self.model)
        view = MainView(self.app, controller=controller)
        controller.view = view

    def user_state_changed(self, *args):
        if self.user_logged_state.get() is True:
            for widget in self.app.slaves():
                widget.destroy()

            self.app.geometry('500x400')
            self.start_main_view()


class MainViewController(GenericController):
    def __init__(self, app: Tk, sock: socket, model: User, view: MainView = None):
        super().__init__(app, sock, model, view)
        self.response_receive_handler = Thread(target=self.receive_response)
        self.response_receive_handler = Thread(target=self.receive_response)
        self.response_receive_handler.start()
        self.received_responses = Queue()
        self.response_handler = Thread(target=self.treat_responses)
        self.response_handler.start()
        self.received_messages = Queue()
        self.received_messages_handler = Thread(target=self.receive_messages)
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
                elif len(received) < 4096:
                    data += received
                    break
                else:
                    data += received

            self.received_responses.put(json.loads(data.decode()))

    def treat_responses(self):
        while True:
            while self.received_responses.empty() is False:
                response = self.received_responses.get()

                if 'message' in response or 'fetched_message' in response:
                    self.received_messages.put(response)
                elif 'info' in response:
                    messagebox.showinfo('Server response', response['info'])
                elif 'search_result' in response:
                    result = response['search_result']

                    if result['info'].endswith('exist'):
                        messagebox.showinfo('Server response', result['info'])
                    else:
                        self.view.active_chat['state'] = 'normal'
                        self.view.message_entry['state'] = 'normal'
                        self.view.send_message_button['state'] = 'normal'
                        self.view.active_chat.delete(0, END)
                        self.send_request({'request': 'prefetch_messages'})

    def receive_messages(self):
        while True:
            if self.received_messages.empty() is False:
                response = self.received_messages.get()
                is_fetched = 'fetched_message' in response
                json_message = response['message'] if 'message' in response else response['fetched_message']

                if json_message['sender'] == self.model.username:
                    json_message['sender'] = 'Você'

                message = '{}: {}'.format(json_message['sender'], json_message['content'])
                if is_fetched:
                    self.view.active_chat.insert(0, message)
                else:
                    self.view.active_chat.insert(END, message)
            time.sleep(0.05)

    def search_username_changed(self, *args):
        username = self.view.search_username.get()

        if len(username) >= 8:
            self.view.search_button['state'] = 'normal'
        else:
            self.view.search_button['state'] = 'disabled'

    def search_user(self, *args):
        username = self.view.search_username.get()

        request = {
            'request': 'search_for',
            'username': username
        }

        self.send_request(request)

    def message_changed(self, *args):
        if len(self.view.message.get()) > 0:
            self.view.send_message_button['state'] = 'normal'
        else:
            self.view.send_message_button['state'] = 'disabled'

    def send_message(self, *args):
        request = {
            'request': 'send_message',
            'message': {
                'sender': self.model.username,
                'content': self.view.message_entry.get(),
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 1
            }
        }

        self.send_request(request)

# if __name__ == '__main__':
#     p = 'testPass123'
#     hasher = sha256(p.encode())
#     print(hasher.hexdigest())
#     print('cb92d111bf8d6bcf59e905d5fc50d5d403f0a59bf9a857b711020ba083b524a9')
