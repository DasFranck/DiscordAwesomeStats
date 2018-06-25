from peewee import (Model, SqliteDatabase, 
                    IntegerField, CharField, 
                    ForeignKeyField, TextField)

db = SqliteDatabase('database.db')

class BaseModel(Model):
    class Meta:
        database = db


class Server(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField()


class Channel(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField()
    server = ForeignKeyField(Server)


class Member(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField() 
    nick = CharField()
    discriminator = CharField(4)


class Message(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    server_id = ForeignKeyField(Server, backref='messages')
    channel_id = ForeignKeyField(Channel, backref='messages')
    author_id = ForeignKeyField(Member, backref='messages')
    timestamp = IntegerField()


class Message_count(BaseModel):
    author_id = ForeignKeyField(Member)
    server_id = ForeignKeyField(Server)
    channel_id = ForeignKeyField(Channel)
    date = CharField()
    count = IntegerField()

    class Meta:
        indexes = (
            (('author_id', 'server_id', 'channel_id', 'date'), True),
        )