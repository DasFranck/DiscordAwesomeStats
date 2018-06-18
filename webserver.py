from flask import Flask
app = Flask("Discord Awesome Stats")

@app.route('/')
def root():
    return ("Welcome")