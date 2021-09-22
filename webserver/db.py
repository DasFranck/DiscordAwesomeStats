import sqlite3

from contextlib import closing

from flask import g

def get_guilds():
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild;").fetchall()

def get_guild(guild_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild WHERE guild_id IS ?", (guild_id,)).fetchone()

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