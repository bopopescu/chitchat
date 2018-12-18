from src import server_host
from src.Models import User, Message
from src.DAO import UserDAO, MessageDAO
from threading import Thread, Lock, current_thread
from queue import Queue
import json
import socket
import mysql.connector as mysql


class Server:
    def __init__(self):
        self.database_connection = mysql.connect(
            host='localhost',
            user='root',
            password='',
            database='chitchatdb'
        )
        self.cursor = self.database_connection.cursor()
        self.userDAO = UserDAO(self.database_connection)
        self.messageDAO = MessageDAO(self.database_connection)
        self.host = server_host.host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.host)
        self.socket.listen(5)
        self.connected_clients = {}
        self.lock = Lock()
        self.messages_queue = Queue()

    def run(self):
        while True:
            print('Waiting for connection')
            client_connection, client_address = self.socket.accept()

            print('Client at {} connected'.format(client_address))
            Thread(target=self.handle_connection, args=(client_connection,)).start()

    def handle_connection(self, client_connection: socket.socket):
        thread_name = current_thread().getName()
        print('\t{}: Started'.format(thread_name))

        try:
            while True:
                data = bytes()
                received = bytes()

                while True:
                    received += client_connection.recv(4096)
                    if not received:
                        break
                    else:
                        data += received

                request = json.loads(data.decode())

                if request['request'] == 'login' or request['request'] == 'register':
                    user_data = request['user']
                    user = User(user_data['username'], user_data['password'])

                    if request['request'] == 'login':
                        print('\t{}: Checking if user is registered'.format(thread_name))
                        user.id = self.userDAO.get_user_id(user)

                        if user.id == 0:
                            print('\t{}: User is not registered'.format(thread_name))
                            response = {'info': 'Invalid username or password'}
                        else:
                            print('\t{}: User logged in'.format(thread_name))
                            self.connected_clients[client_connection.fileno()] = user.id
                            response = {'info': 'Logged'}
                    else:
                        print('\t{}: Trying to add user to the database'.format(thread_name))
                        user = self.userDAO.insert(user)

                        if user is None:
                            print('\t{}: User already exists'.format(thread_name))
                            response = {'info': 'User already exists'}
                        else:
                            print('\t{}: User registered'.format(thread_name))
                            response = {'info': 'Successfully registered'}

                    client_connection.sendall(json.dumps(response).encode())

                    if response['info'] == 'Invalid username or password' or \
                       response['info'] == 'User already exists':
                        break
                elif request['request'] == 'prefetch_messages':
                    print('\t{}: Fetching user messages'.format(thread_name))
                    user_id = self.connected_clients[client_connection.fileno()]
                    other_id = self.userDAO.get_id_by_username(request['with'])

                    if other_id == 0:
                        response = {'info': '{} does not exist'.format(request['with'])}
                        client_connection.sendall(json.dumps(response).encode())
                    else:
                        messages = self.messageDAO.prefetch(user_id, other_id, 20)

                        for message in messages:
                            json_message = {
                                'message': {
                                    'sender': self.userDAO.get_user_by_id(message.sender_id),
                                    'content': message.content
                                }
                            }
                            client_connection.sendall(json.dumps(json_message).encode())
                elif request['request'] == 'send_message':
                    pass

        except ConnectionError or Exception as err:
            client_connection.close()

            for _id, connection in self.connected_clients.items():
                if connection == client_connection:
                    with self.lock:
                        self.connected_clients.pop(_id)
                        break
            raise err

        finally:
            print('\t{}: Connection closed'.format(thread_name))
            client_connection.close()


if __name__ == '__main__':
    server = Server()
    server.run()
