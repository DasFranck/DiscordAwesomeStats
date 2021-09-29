import functools
import operator
import time
from contextlib import closing

from datetime import date
from dateutil.rrule import rrule, MONTHLY
from typing import List, Tuple

from flask import Blueprint, render_template, flash, redirect, url_for, g

from .db import get_db, get_guild, get_guilds, get_member_active_channels_guilds, get_channels, get_member, get_guild_members

frontend = Blueprint('frontend', __name__)


def get_message_count_per_date(guild_id: int = 0, channel_ids: List[int] = [], member_id: int = 0):
    message_count_per_date = {}
    with closing(get_db().cursor()) as cursor:
        if guild_id and not channel_ids:
            channel_ids = [channel[0] for channel in cursor.execute("""
                SELECT channel_id, channel_name
                FROM channel
                WHERE guild_id = ?
                """, (guild_id,)).fetchall()]
        if not channel_ids:
            #throw exception here
            pass
        for channel_id in channel_ids:
            for count in cursor.execute("""
                SELECT date, SUM(count), member_id
                FROM daily_message_count
                WHERE channel_id LIKE ? AND member_id LIKE ? GROUP BY date;
                """, (channel_id if channel_id else "%", member_id if member_id else "%")).fetchall():
                message_count_date = str(count[0])
                if message_count_date in message_count_per_date:
                    message_count_per_date[message_count_date] += count[1]
                else:
                    message_count_per_date[message_count_date] = count[1]
    return message_count_per_date

def get_message_count_per_month(guild_id: int = 0, channel_ids: List[int] = [], member_id: int = 0, message_count_per_date = None):
    if not message_count_per_date:
        message_count_per_date = get_message_count_per_date(guild_id, channel_ids, member_id)

    return {
        month.strftime("%B %Y"): 
            sum([message_count_per_date[date] for date in message_count_per_date if date.startswith(month.strftime("%Y-%m"))]) 
        for month in rrule(MONTHLY, dtstart=date.fromisoformat(min(message_count_per_date.keys())), until=date.today())
    }

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
def index_page():
    return render_template('index.html.j2')

@frontend.route("/stats")
def stats_page():
    return ""

@frontend.route("/guild/<int:guild_id>")
def guild_id_page(guild_id: int):
    message_count_per_date = get_message_count_per_date(guild_id=guild_id)
    message_count_per_month = get_message_count_per_month(message_count_per_date=message_count_per_date)

    return render_template(
        'guild_id.html.j2', 
        target_guild=get_guild(guild_id), 
        message_count_per_date=message_count_per_date,
        message_count_per_month=message_count_per_month,
        busyest_date=max(message_count_per_date, key=message_count_per_date.get),
        busyest_month=max(message_count_per_month, key=message_count_per_month.get),
        channels=get_channels(guild_id),
        member_list=get_guild_members(guild_id)
    )

@frontend.route("/member/")
def member_page():
    return ""

@frontend.route("/member/<int:member_id>")
def member_id_page(member_id: int):
    member = get_member(member_id=member_id)
    active_channels_guilds = get_member_active_channels_guilds(member_id)
    message_count_per_date_dict = {
        channel[0]:
            get_message_count_per_date(member_id=member_id, channel_ids=[channel[0]]) for channel in functools.reduce(operator.iconcat, active_channels_guilds.values(), [])
    }
    message_count_per_month_dict = {
        channel[0]:
            get_message_count_per_month(member_id=member_id, channel_ids=[channel[0]]) for channel in functools.reduce(operator.iconcat, active_channels_guilds.values(), [])
    }

    return render_template(
        'member_id.html.j2',
        member_name=member[1],
        member_discriminator=member[2],
        active_channels_guilds=active_channels_guilds,
        message_count_per_date_dict=message_count_per_date_dict,
        message_count_per_month_dict=message_count_per_month_dict
    )


@frontend.route("/channel/<int:channel_id>")
def channel_id_page(channel_id: int):
    return ""