import requests
import json
import datetime as dt


class Musicsenseclient():

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.cookies = None
        self.context = {"time": "2016-11-01 14:10:45", "ip": '8.8.8.8', "location": "disabled", "locale": "en-US",
                        "device": "browser"}

    def ping(host='http://musicsense.me'):
        url= '%s/api/ping' % host
        response = requests.get(url=url)
        if response.status_code == 200:
            return True
        return False

    def login(self):

        url = '%s/api/users/login' % self.host

        try:
            signin = requests.post(url, data={'account': self.username, 'password': self.password})
        except:
            return False

        self.cookies = signin.cookies

        return True

    def musicfeed_suggest(self, q, tracksEnabled=True, limit=20):
        url = '%s/api/musicfeed/suggest' % self.host
        response = requests.post(url, data={'limit': limit, 'tracksEnabled': tracksEnabled, 'q': q},
                                        cookies=self.cookies)
        suggest = {}
        suggest['data'] = json.loads(response.text)

        return suggest

    def musicfeed_generate(self, type, artist, title, typeSource):
        time_now = dt.datetime.now()
        time = time_now.strftime("%Y-%m-%d %H:%M:%S")
        self.context['time'] = time
        url = '%s/api/musicfeed/generate' % self.host
        payload = {
            'type': type,
            'context': json.dumps(self.context),
            'artist': artist,
            'title': title,
            'typeSource': typeSource
        }
        headers = {}
        headers['Content-Type'] = 'application/json'
        response = requests.post(url, data=payload, cookies=self.cookies, headers=headers)
        generate = {}
        generate['data'] = json.loads(response.text)

        return generate

    def musicfeed_songs(self, feed_id, limit=20, offset=0):
        url = '{host}/api/musicfeed/{feed_id}/songs'.format(host=self.host, feed_id=feed_id)
        payload = {'limit': limit, 'offset': offset}
        response = requests.post(url, data=payload, cookies=self.cookies)
        songs = {}
        songs['data'] = json.loads(response.text)

        return songs

    def musicfeed_stream(self, id):
        url = '{host}/api/music/stream/{id}'.format(host=self.host, id=id)
        response = requests.get(url, cookies=self.cookies, stream=True)
        stream = {}
        stream['data'] = response.raw

        return stream

    def helper_generate_songs(self, type, artist, title, typeSource, limit=20, offset=0):
        generate = self.musicfeed_generate(type, artist, title, typeSource)
        feed_id = generate['data']["result"]
        songs = self.musicfeed_songs(feed_id, limit, offset)
        
        return songs




