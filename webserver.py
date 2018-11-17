from flask import Flask, render_template, url_for

app = Flask("Discord Awesome Stats")

@app.route('/')
def root():
    return render_template("index.html.j2", guild_channel_dict={})

if __name__ == '__main__':
    app.run(debug=True)