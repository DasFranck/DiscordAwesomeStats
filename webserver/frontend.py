from flask import Blueprint, render_template, flash, redirect, url_for
from markupsafe import escape


frontend = Blueprint('frontend', __name__)



def get_guilds():
    pass


@frontend.route('/')
def index():
    return render_template('index.html.j2', guilds=get_guilds())

@frontend.route("/stats")
def stats():
    return ""

@frontend.route("/guild/")
def guild():
    return ""

@frontend.route("/guild/<int:guild_id>")
def guild_id():
    return ""

@frontend.route("/user/")
def user():
    return ""

@frontend.route("/user/<int:user_id>")
def user_id():
    return ""