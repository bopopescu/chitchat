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
            print('\t{}: Waiting for request'.format(thread_name))

            data = bytes()
            while True:
                received = client_connection.recv(4096)
                if received is None:
                    break
                elif len(received) < 4096:
                    data += received
                    break
                else:
                    data += received

            request = json.loads(data.decode())
            print('\t{}: Received request {}'.format(thread_name, request))

            user_data = request['user']
            user = User(user_data['username'], user_data['password'])

            if request['request'] == 'login' or request['request'] == 'register':
                if request['request'] == 'login':
                    print('\t{}: Checking if user is registered'.format(thread_name))
                    # TODO solve * 'str' object has no attribute 'username' * problem
                    # user.id = self.userDAO.get_user_id(user.username)

                    if user.id == 0:
                        print('\t{}: User is not registered'.format(thread_name))
                        client_connection.sendall(json.dumps({'message': 'Invalid username or password'}).encode())
                        raise Exception('Disconnecting client')
                    else:
                        print('\t{}: User logged in'.format(thread_name))
                        client_connection.sendall(json.dumps({'message': 'Logged'}))
                else:
                    print('\t{}: Trying to add user to the database'.format(thread_name))
                    user = self.userDAO.insert(user)

                    if user is None:
                        print('\t{}: User already exists'.format(thread_name))
                        client_connection.sendall(json.dumps({'message': 'User already exists'}).encode())
                        raise Exception('Disconnecting client')
                    else:
                        print('\t{}: User registered'.format(thread_name))
                        client_connection.sendall(json.dumps({'message': 'Successfully registered'}).encode())

            while True:
                print('\t{}: Waiting for user to send a message'.format(thread_name))

                data = client_connection.recv(4096)
                while data:
                    data += client_connection.recv(4096)

                print('\t{}: Message received'.format(thread_name))

                json_message = json.loads(data.decode())
                message = Message.from_json(json_message)
                self.messageDAO.insert(message)
                print('\t{}: Added message to database'.format(thread_name))

                if json_message['receiver_id'] in self.connected_clients.keys():
                    receiver_connection = self.connected_clients[json_message['receiver_id']]
                    receiver_connection.sendall(json_message)
                    print('\t{}: Sent message to its receiver'.format(thread_name))

        except ConnectionError or Exception as err:
            client_connection.close()

            for _id, connection in self.connected_clients.items():
                if connection == client_connection:
                    self.connected_clients.pop(_id)
                    break

            raise err


if __name__ == '__main__':
    server = Server()
    server.run()
