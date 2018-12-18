import mysql.connector as mysql
from mysql.connector import MySQLConnection
from src.Models import User, Message


class GenericDAO:
    def __init__(self, connection: MySQLConnection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def execute(self, query: str):
        self.cursor.execute(query)

    def commit(self):
        self.connection.commit()

    def fetchone(self, *args):
        pass

    def fetchall(self, *args):
        pass

    def insert(self, *args):
        pass

    def remove(self, *args):
        pass

    def update(self, *args):
        pass


class UserDAO(GenericDAO):
    def __init__(self, connection: MySQLConnection):
        super().__init__(connection)

    def fetchone(self):
        fetch_result = self.cursor.fetchone()

        if fetch_result is not None:
            _id, username, password = fetch_result
            return User(username, password, _id=_id)
        else:
            return None

    def fetchall(self):
        query = 'SELECT * FROM user'
        self.cursor.execute(query)

        return [
            User(username, password, _id=_id)
            for _id, username, password in self.cursor.fetchall()
        ]

    def insert(self, user: User):
        self.cursor.callproc('add_user', (user.username, user.password))

    def remove(self, user: User):
        self.cursor.callproc('rmv_user', user.username)

    def update(self, user: User):
        query = 'CALL update_user({}, \'{}\', \'{}\');'.format(user.id, user.username, user.password)
        self.execute(query)
        self.commit()

        return self.fetchone()

    def get_user_by_id(self, user_id: int):
        result = self.cursor.callproc('get_user_by_id', (user_id, ('username', 'password')))
        return {'username': result[2][0], 'password': result[2][1]}

    def get_user_id(self, user: User):
        result = self.cursor.callproc('get_user_id', (user.username, user.password, '_id'))
        return 0 if result[2] is None else result[2]

    def get_id_by_username(self, username: str):
        self.cursor.execute('SELECT id FROM `user` WHERE username = \'{}\''.format(username))
        result = self.cursor.fetchone()

        return 0 if result is None else result[0]


class MessageDAO(GenericDAO):
    def __init__(self, connection: MySQLConnection):
        super().__init__(connection)

    def fetchone(self, username: str):
        pass

    def fetchall(self):
        return self.cursor.fetchall()

    def insert(self, message: Message):
        query = 'CALL add_message(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\');'.format(message.sender_id,
                                                                                   message.receiver_id,
                                                                                   message.content,
                                                                                   message.status,
                                                                                   message.send_time)
        self.execute(query)
        self.commit()

    def remove(self, *args):
        pass

    def update(self, *args):
        pass

    def prefetch(self, user_id: int, other_id: int, num_of_messages: int):
        query = 'SELECT * FROM message \n\
                 WHERE (sender_id = {user_id} AND receiver_id = {other_id}) \
                 OR (sender_id = {other_id} AND receiver_id = {user_id}) \n\
                 ORDER BY send_time DESC \n\
                 LIMIT {quantity}'.format(user_id=user_id, other_id=other_id, quantity=num_of_messages)
        self.execute(query)

        return [
            Message(sender_id=msg_data[1],
                    receiver_id=msg_data[2],
                    _id=msg_data[0],
                    content=msg_data[3],
                    send_time=msg_data[4],
                    status=msg_data[5])
            for msg_data in self.fetchall()
        ]


# if __name__ == '__main__':
#     database_connection = mysql.connect(
#         host='localhost',
#         user='root',
#         password='',
#         database='chitchatdb'
#     )
#     cursor = database_connection.cursor()
#     query = ''
#
#     cursor.execute(query)
#     result = cursor.fetchall()
