import sqlite3

from contextlib import closing
from typing import List, Tuple

from flask import g

def get_member(member_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM member WHERE member_id IS ?", (member_id,)).fetchone()

def get_guilds():
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild;").fetchall()

def get_guild(guild_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild WHERE guild_id IS ?", (guild_id,)).fetchone()

def get_channel(channel_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM channel WHERE channel_id IS ?", (channel_id,)).fetchone()

def get_channels(guild_id: int) -> List[Tuple[int, str]]:
    with closing(get_db().cursor()) as cursor:
        return [channel for channel in cursor.execute("SELECT channel_id, channel_name FROM channel WHERE guild_id = ?", (guild_id,)).fetchall()]

def get_member_active_channels_servers(member_id: int) -> Tuple[List[str], List[str]]:
    with closing(get_db().cursor()) as cursor:
        return {
            [channel[0] for channel in cursor.execute("SELECT DISTINCT channel_id FROM daily_message_count WHERE member_id = ?;", (member_id,)).fetchall()],
            [guild[0] for guild in cursor.execute("SELECT DISTINCT channel_id FROM daily_message_count LEFT JOIN guild ON channel_id = guild.guild_id WHERE member_id = ?;", (member_id,)).fetchall()]
        }

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            "das.db",
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()