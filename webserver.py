from flask import Flask, render_template, url_for

@app.route('/')
def root():
    return render_template("index.html.j2", server_channel_dict={})

if __name__ == '__main__':
    app = Flask("Discord Awesome Stats")
    app.run(debug=True)