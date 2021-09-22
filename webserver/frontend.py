import time
from contextlib import closing
from typing import OrderedDict

from datetime import date
from dateutil.rrule import rrule, MONTHLY
from flask import Blueprint, render_template, flash, redirect, url_for, g
from markupsafe import escape

from .db import get_db

frontend = Blueprint('frontend', __name__)

def get_guilds():
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild;").fetchall()

def get_guild(guild_id: int):
    with closing(get_db().cursor()) as cursor:
        return cursor.execute("SELECT * FROM guild WHERE guild_id IS ?", (guild_id,)).fetchone()

@frontend.before_request
def before_request():
  g.start = time.time()

@frontend.after_request
def after_request(response):
    diff = time.time() - g.start
    if (response.response and
        200 <= response.status_code < 300 and
        response.content_type.startswith('text/html')):
        response.set_data(response.get_data().replace(
            b'__EXECUTION_TIME__', bytes(str(diff), 'utf-8')))
    return response

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
    message_count_per_date = {}
    with closing(get_db().cursor()) as cursor:
        channels = cursor.execute("SELECT channel_id, channel_name FROM channel WHERE guild_id = ?", (guild_id,)).fetchall()
        for channel in channels:
            for count in cursor.execute("SELECT date, SUM(count), member_id FROM daily_message_count WHERE channel_id = ? GROUP BY date;", (channel[0],)).fetchall():
                message_count_date = str(count[0])
                if message_count_date in message_count_per_date:
                    message_count_per_date[message_count_date] += count[1]
                else:
                    message_count_per_date[message_count_date] = count[1]

    message_count_per_month = {month.strftime("%B %Y"): sum([message_count_per_date[date] for date in message_count_per_date if date.startswith(month.strftime("%Y-%m"))]) for month in rrule(MONTHLY, dtstart=date.fromisoformat(min(message_count_per_date.keys())), until=date.today())}

    return render_template(
        'guild_id.html.j2', 
        target_guild=get_guild(guild_id), 
        message_count_per_date=message_count_per_date,
        message_count_per_month=message_count_per_month,
        busyest_date=max(message_count_per_date, key=message_count_per_date.get),
        busyest_month=max(message_count_per_month, key=message_count_per_month.get),
        channels=channels
    )

@frontend.route("/user/")
def user():
    return ""

@frontend.route("/user/<int:user_id>")
def user_id(user_id: int):
    return ""