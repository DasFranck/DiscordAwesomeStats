from peewee import (Model, SqliteDatabase, 
                    IntegerField, CharField, 
                    ForeignKeyField, TextField,
                    BooleanField, CompositeKey)

database = SqliteDatabase('database.db')

class BaseModel(Model):
    class Meta:
        database = database


class Guild(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField()
    members = CharField()


class Channel(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField()
    guild = ForeignKeyField(Guild)


class Member(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    name = CharField() 
    discriminator = CharField(4)


class Nick(BaseModel):
    member_id = ForeignKeyField(Member)
    guild_id = ForeignKeyField(Guild)
    nick = CharField()

    class Meta:
        indexes = (
            (('member_id', 'guild_id'), True),
        )
        primary_key = CompositeKey('member_id', 'guild_id')


class Message(BaseModel):
    id = IntegerField(unique=True, primary_key=True)
    channel_id = ForeignKeyField(Channel, backref='messages')
    author_id = ForeignKeyField(Member, backref='messages')
    created_at = IntegerField()

class MessageCountChannel(BaseModel):
    channel_id = ForeignKeyField(Channel)
    date = CharField()
    count = IntegerField()
    cumulative_count = IntegerField()

    class Meta:
        indexes = (
            (('channel_id', 'date'), True),
        )

class MessageCountUserChannel(BaseModel):
    author_id = ForeignKeyField(Member)
    channel_id = ForeignKeyField(Channel)
    date = CharField()
    count = IntegerField()
    cumulative_count = IntegerField()

    class Meta:
        indexes = (
            (('author_id', 'channel_id', 'date'), True),
        )