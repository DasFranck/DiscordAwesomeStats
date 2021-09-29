import sqlite3

from contextlib import closing
from typing import List, Tuple, Dict

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

def get_guild_members(guild_id: int) -> List[Tuple[int, int]]:
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("""
            SELECT member.member_id, member.member_name, member.discriminator, SUM(daily_message_count.count) 
            FROM daily_message_count 
            JOIN channel ON daily_message_count.channel_id IS channel.channel_id
            JOIN member ON daily_message_count.member_id IS member.member_id
            WHERE channel.guild_id IS ?
            GROUP BY member.member_id;
            """, (guild_id,)).fetchall()

def get_channel(channel_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM channel WHERE channel_id IS ?", (channel_id,)).fetchone()

def get_channels(guild_id: int) -> List[Tuple[int, str]]:
    with closing(get_db().cursor()) as cursor:
        return [channel for channel in cursor.execute("SELECT channel_id, channel_name FROM channel WHERE guild_id = ?", (guild_id,)).fetchall()]

def get_member_active_channels_guilds(member_id: int) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    member_active_channels = {}
    with closing(get_db().cursor()) as cursor:
        for guild in cursor.execute("""
            SELECT channel.guild_id, channel.guild_name
            FROM daily_message_count
            LEFT JOIN channel ON daily_message_count.channel_id = channel.channel_id
            WHERE member_id = ?
            GROUP BY channel.guild_id;
            """, (member_id,)).fetchall():
            member_active_channels[guild[0]] = [channel[0] for channel in cursor.execute("""
                SELECT daily_message_count.channel_id, channel.channel_name
                FROM daily_message_count
                JOIN channel ON daily_message_count.channel_id = channel.channel_id
                WHERE member_id = ? AND guild_id = ?
                GROUP BY daily_message_count.channel_id;
                """, (member_id, guild[0])).fetchall()]
    return member_active_channels

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