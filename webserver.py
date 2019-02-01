from flask import Flask, render_template, url_for
from database import Guild


app = Flask("Discord Awesome Stats")

@app.route('/')
def index_page():
    return render_template("index.html.j2", guild_channel_dict={})

@app.route('/guild/<int:guild_id>')
def guild_page(guild_id):
    return render_template("guild_page.html.j2")

@app.route('/channel/<int:channel_id>')
def channel_page(channel_id):
    return render_template("channel_page.html.j2")

if __name__ == '__main__':
    app.run(debug=True)