from peewee import (Model, SqliteDatabase, 
                    IntegerField, CharField, 
                    ForeignKeyField, TextField,
                    BooleanField, CompositeKey)

database = SqliteDatabase('database.db')

class BaseModel(Model):
    class Meta:
        database = database


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
    discriminator = CharField(4)


class Nick(BaseModel):
    member_id = ForeignKeyField(Member)
    server_id = ForeignKeyField(Server)
    nick = CharField()

    class Meta:
        indexes = (
            (('member_id', 'server_id'), True),
        )
        primary_key = CompositeKey('member_id', 'server_id')


class Message(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    channel_id = ForeignKeyField(Channel, backref='messages')
    author_id = ForeignKeyField(Member, backref='messages')
    timestamp = IntegerField()

class Message_count_channel(BaseModel):
    channel_id = ForeignKeyField(Channel)
    date = CharField()
    count = IntegerField()
    cumulative_count = IntegerField()

    class Meta:
        indexes = (
            (('channel_id', 'date'), True),
        )

class Message_count_user(BaseModel):
    author_id = ForeignKeyField(Member)
    channel_id = ForeignKeyField(Channel)
    date = CharField()
    count = IntegerField()

    class Meta:
        indexes = (
            (('author_id', 'channel_id', 'date'), True),
        )