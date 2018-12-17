from datetime import datetime
from enum import Enum


class MessageStatus(Enum):
    SENT = 1
    RECEIVED = 2
    READ = 3


class GenericModel:
    def __init__(self, _id):
        self.id = _id

    def to_json(self):
        raise NotImplementedError('to_json method must be implemented')


class User(GenericModel):
    def __init__(self, username='', password='', _id=0):
        super().__init__(_id)
        self.username = username
        self.password = password
        self.logged = False

    def to_json(self):
        return self.__dict__


class Message(GenericModel):
    def to_json(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'send_time': self.send_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
        }

    def __init__(self,
                 sender_id: int,
                 receiver_id: int,
                 _id=0,
                 content='',
                 send_time=datetime.now(),
                 status=1):
        super().__init__(_id)
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.send_time = send_time
        self.status = status

    @staticmethod
    def from_json(json_message: dict):
        return Message(json_message['sender_id'],
                       json_message['receiver_id'],
                       json_message['content'],
                       json_message['status'],
                       json_message['send_time'])
