from contextlib import closing
from typing import OrderedDict

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
    message_count_per_date = OrderedDict()

    with closing(get_db().cursor()) as cursor:
        for channel_id in cursor.execute("SELECT channel_id FROM channel WHERE guild_id = ?", (guild_id,)).fetchall():
            for count in cursor.execute("SELECT date, SUM(count), member_id FROM daily_message_count WHERE channel_id = ? GROUP BY date;", (channel_id[0],)).fetchall():
                date = str(count[0])
                if date in message_count_per_date:
                    message_count_per_date[date] += count[1]
                else:
                    message_count_per_date[date] = count[1]

    return render_template(
        'guild_id.html.j2', 
        target_guild=get_guild(guild_id), 
        message_count_per_date=message_count_per_date, 
    )

@frontend.route("/user/")
def user():
    return ""

@frontend.route("/user/<int:user_id>")
def user_id(user_id: int):
    return ""