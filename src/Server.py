from Models import User, Message
from DAO import UserDAO, MessageDAO
from threading import Thread, Lock, current_thread, local
from queue import Queue
import server_host
import time
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
            local_data = local()
            while True:
                data = bytes()
                received = bytes()

                while True:
                    received += client_connection.recv(4096)
                    if not received:
                        break
                    elif len(received) < 4096:
                        data += received
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
                            local_data.user = user
                            self.connected_clients[local_data.user.id] = client_connection
                            response = {'info': 'Logged'}
                    else:
                        print('\t{}: Trying to add user to the database'.format(thread_name))
                        user = self.userDAO.insert(user)

                        if user is None:
                            print('\t{}: User already exists'.format(thread_name))
                            response = {'info': 'User already exists'}
                        else:
                            print('\t{}: User registered'.format(thread_name))
                            local_data.user = user
                            response = {'info': 'Successfully registered'}

                    client_connection.sendall(json.dumps(response).encode())

                    if response['info'] == 'Invalid username or password' \
                       or response['info'] == 'User already exists':
                        break
                elif request['request'] == 'search_for':
                    print('\t{}: Searching for user'.format(thread_name))
                    other_id = self.userDAO.get_id_by_username(request['username'])

                    if other_id == 0:
                        response = {'search_result': {'info': '{} does not exist'.format(request['username'])}}
                        client_connection.sendall(json.dumps(response).encode())
                    else:
                        json_user = self.userDAO.get_user_by_id(other_id)
                        local_data.other_client = User(json_user['username'], json_user['password'], _id=other_id)
                        response = {'search_result': {'info': '{} found'.format(request['username'])}}
                        client_connection.sendall(json.dumps(response).encode())
                elif request['request'] == 'prefetch_messages':
                    print('\t{}: Fetching user messages'.format(thread_name))
                    messages = self.messageDAO.prefetch(local_data.user.id, local_data.other_client.id, 20)

                    for message in messages:
                        if message.sender_id == local_data.user.id:
                            sender_username = local_data.user.username
                        else:
                            sender_username = local_data.other_client.username

                        json_message = {
                            'message': {
                                'sender': sender_username,
                                'content': message.content
                            }
                        }
                        client_connection.sendall(json.dumps(json_message).encode())
                        time.sleep(0.08)
                elif request['request'] == 'send_message':
                    json_message = request['message']
                    message = Message(local_data.user.id,
                                      local_data.other_client.id,
                                      content=json_message['content'],
                                      send_time=json_message['send_time'],
                                      status=1)
                    self.messageDAO.insert(message)
                    message = {
                        'message': {
                            'sender': local_data.user.username,
                            'content': json_message['content']
                        }
                    }
                    client_connection.sendall(json.dumps(message).encode())

                    if local_data.other_client.id in self.connected_clients.keys():
                        connection = self.connected_clients[local_data.user.id]
                        connection.sendall(json.dumps({'message': message}).encode())

        except ConnectionError or Exception:
            print('\t{}: Some error happened, connection will be closed'.format(thread_name))
            client_connection.close()

            for _id, connection in self.connected_clients.items():
                if connection == client_connection:
                    with self.lock:
                        self.connected_clients.pop(_id)
                        break

        finally:
            print('\t{}: Connection closed'.format(thread_name))
            client_connection.close()


if __name__ == '__main__':
    server = Server()
    server.run()

