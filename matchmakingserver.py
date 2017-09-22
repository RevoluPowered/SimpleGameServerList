#!/usr/bin/env python

# note: we are using pipenv and python 3.6.1
from sys import stdout
from bottle import request, route, run, get, post

@route('/')
def index():
    return "server is up"


@get('/matchmaking/create')
def create_match_debug():
    return '''
        <h3>Game info</h3>
        <form action="/matchmaking/create" method="post">
            Name: <input name="name" type="text" />
            Password: <input name="password" type="password" />
            Players: <input name ="maxplayers" type="number"/>
            <input value="Create Game" type="submit" />
        </form>
    '''

@post('/matchmaking/create')
def create_match():
    gamename = request.forms.get('name')
    password = request.forms.get('password')
    count = request.forms.get('maxplayers')
    stdout.write("creating " + gamename + " with password: " + password + " count: " + count)
    return "creating " + gamename + " with password: " + password + " count: " + count




run(host='localhost', port=8080, debug=True)