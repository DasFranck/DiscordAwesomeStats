from contextlib import closing

from flask import Blueprint, render_template, flash, redirect, url_for
from markupsafe import escape

from .db import get_db

frontend = Blueprint('frontend', __name__)

def get_guilds():
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild;").fetchall()

def get_guild(guild_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild WHERE guild_id IS ?", (guild_id,)).fetchone()

@frontend.context_processor
def inject_guilds():
    return dict(guild_list=get_guilds())

@frontend.route('/')
def index():
    return render_template('index.html.j2')

@frontend.route("/stats")
def stats():
    return ""

@frontend.route("/guild/")
def guild():
    return ""

@frontend.route("/guild/<int:guild_id>")
def guild_id(guild_id: int):
    with closing(get_db().cursor()) as cursor:
        for channel_id in cursor.execute("SELECT channel_id FROM channel WHERE guild_id = ?", (guild_id,)).fetchall()[0]:
            message_count_per_date = cursor.execute("SELECT date, SUM(count), member_id FROM daily_message_count WHERE channel_id = ? GROUP BY date;", (channel_id,)).fetchall()

    date_axis = [str(message_count[0]) for message_count in message_count_per_date]
    count_axis = [message_count[1] for message_count in message_count_per_date]
    return render_template('guild_id.html.j2', target_guild=get_guild(guild_id), date_axis=date_axis, count_axis=count_axis)

@frontend.route("/user/")
def user():
    return ""

@frontend.route("/user/<int:user_id>")
def user_id(user_id: int):
    return ""