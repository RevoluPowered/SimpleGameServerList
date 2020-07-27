#!/usr/bin/env python
# note: we are using pipenv and python 3.6.1
from gevent import monkey; monkey.patch_all()
from sys import stdout
import json
from bottle import request, route, run, get, post
from logging import basicConfig, debug, info, warning, DEBUG
from collections import namedtuple


basicConfig(filename='matchmakingserver.log', level=DEBUG)

Endpoint = namedtuple('Endpoint', ['address', 'port'] )

# Webserver and Code Debugging?
#DEBUG_SERVER = False
DEBUG_SERVER = True

class Match:
    """ match data container """

    matches = []

    def __init__(self, gamename, password, max_players, server_address, server_port):
        """ initialise a new match """
        self.gamename = gamename
        self.max_players = max_players
        self.player_count = 0
        self.server_address = server_address
        self.server_port = server_port

        if password is None:
            debug("server has no password.")
            self.server_password = ""
        else:
            debug("server registered with password.")
            self.server_password = password
        
        debug("create new match: " + str(self))
        Match.matches.append(self)


    def request_join(self, _password, _ip):
        """ request join to the server """
        debug("join requested from: " + _ip)
        if self.server_password == _password:
            debug("join successful for " + _ip)
            return Endpoint(str(self.server_address), int(self.server_port))
        else:
            debug("join failed for " + _ip)
            return "incorrect server password"

    @staticmethod
    def join_match(name, password, _ip):
        """ join a match by name, returns server info if the password is correct """
        debug("finding match for " + _ip)

        # do not require a password to be supplied.
        if password is None:
            password = ""

        for match in Match.matches:
            if match.gamename == name:
                return match.request_join(password, _ip)

        return "match not found"

    @staticmethod
    def close_match(name, _ip):
        """ close down a match when the host quits or the dedicated server is closed """
        debug("finding match to close down")

        to_delete = None
        for match in Match.matches:
            if match.gamename == name:
                to_delete = match
        
        if to_delete is not None:
            # remove from list
            Match.matches.remove(to_delete)
            debug("completed deleting match")
            return "closed match"
        else:
            debug("unable to delete match")
            return "match not found"



    def server_info(self):
        match_info = {}
        match_info['name'] = self.gamename
        match_info['max_players'] = self.max_players
        match_info['players'] = self.player_count
        return match_info


    def __str__(self):
        output_str = []
        output_str.append("Game: " + self.gamename)
        output_str.append(", max players: " + str(self.max_players))
        output_str.append(", player count: " + str(self.player_count))
        output_str.append(", address: " + self.server_address)
        output_str.append(", port: " + str(self.server_port))
        output_str.append(", password: " + self.server_password)
        return "".join(output_str)


@route('/')
def index():
    return "server is up"

#
# Debug forms for testing purposes
# remove them in production use

if DEBUG_SERVER:
    @get('/matchmaking/create')
    def create_match_debug():
        """ this is for debugging purposes, returns manual forms for testing the server out """
        return '''
            <h3>Create new game</h3>
            <form action="/matchmaking/create" method="post">
                Name: <input name="name" type="text" />
                Password: <input name="password" type="password" />
                Players: <input name ="maxplayers" type="number" value=10/>
                Port: <input name ="port" type="number" value="27015"/>
                Address: <input name ="address" type="text" value="192.168.0.1"/>
                <input value="Create Game" type="submit" />
            </form>
        '''

    @get('/matchmaking/join')
    def join_match_debug():
        return '''
            <h3>Join game</h3>
            <form action="/matchmaking/join" method="post">
                Name: <input name="name" type="text" />
                Password: <input name="password" type="password" />
                <input value="Join Game" type="submit" />
            </form>
        '''

    @get('/matchmaking/close')
    def close_match_debug():
        return '''
            <h3>Close game</h3>
            <form action="/matchmaking/close" method="post">
                Name: <input name="name" type="text" />               
                <input value="Close Game" type="submit" />
            </form>
        '''

#
# Matchmaking functions
#

@get('/matchmaking/list') 
def list_matches():
    return "{\"servers\":" + json.dumps([match.server_info() for match in Match.matches]) + "}"


@post('/matchmaking/create')
def create_match():
    debug("match requested")
    #debug("request info: " + str(request.forms))
#    return "query check: " + str(request.forms)
    gamename = str(request.forms.get('gamename'))
    password = str(request.forms.get('password') or "")
    count = int(request.forms.get('maxplayers'))
    address = retrieve_ip()
    port = int(request.forms.get('port'))

    # create the match - will be stored internally automatically
    game = Match(gamename, password, count, address, port)
    debug("match created, returning info!")
    return "" + str(game)


def retrieve_ip():
    return request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')


@post('/matchmaking/join')
def join_game():
    gamename = str(request.forms.get('name'))
    password = str(request.forms.get('password') or "")
    # HTTP_X_FORWARDED_FOR is a proxy check, if it returns null the REMOTE_ADDR is used.
    ip = retrieve_ip()
    # post: join match and retrieve endpoint for sending to client
    endpoint = Match.join_match(gamename, password, ip)
    # validate endpoint
    if type(endpoint) is not str:
        # check if this connection is a developer or the same player re-connecting to their own server
        # bad way of handling it but we can fix this later.
        if endpoint.address == ip:
            debug("Found another LAN client redirecting to editor")
            return "" + "127.0.0.1" + ":" + str(endpoint.port)
        else:
            debug("returning known global IP address")
            return "" + endpoint.address + ":" + str(endpoint.port)
    else:
        # will be error message
        return endpoint


@post('/matchmaking/close')
def close_game():
    """ close the game, if it can be found """
    gamename = str(request.forms.get('name') or "")
    # HTTP_X_FORWARDED_FOR is a proxy check, if it returns null the REMOTE_ADDR is used.
    ip = retrieve_ip()
    # post: close the match and return the status of the match to the client
    return Match.close_match(gamename, ip)



run(host='0.0.0.0', port=27014, debug=DEBUG_SERVER, server='gevent')
