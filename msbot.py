import telebot
from telebot import types
import json
import musicsenseapi
import logging
import redis
import uuid as uid

with open("config.json") as json_file:
    config = json.load(json_file)
token = config['telegram']['token']
url = config['musicsense']['url']
username = config['musicsense']['username']
password = config['musicsense']['password']
ms_bot = telebot.TeleBot(token)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

musicsenseapi.Musicsenseclient.ping()
musicsense_client = musicsenseapi.Musicsenseclient(url, username, password)
musicsense_client.login()

redis_client = redis.Redis()


@ms_bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.username
    ms_bot.send_message(message.chat.id, "Привет, {name}! Я помогу тебе найти музыку, которая тебе нравится.\n"
                                         "Набери трек, который хочешь послушать".format(name=name))


@ms_bot.message_handler(content_types=['text'])
def suggest_buttons(message):
    query = message.text
    suggests = musicsense_client.musicfeed_suggest(query, limit=5)
    keyboard = types.InlineKeyboardMarkup()

    if len(suggests['data']['items']) != 0:
        for suggest in suggests['data']['items']:

            if suggest["type"] == "TRACK":
                text = "{artist}~{title}".format(artist=suggest['artist'], title=suggest['title'])
                button_key = str(uid.uuid4())
                call_data = button_key
                button_value = json.dumps({'type': 'suggest',
                                           'data': {'artist': suggest['artist'], 'title': suggest['title']}})
                redis_client.mset({button_key: button_value})
                redis_client.expire(button_key, 86400)
                button = types.InlineKeyboardButton(text=text, callback_data=call_data)
                keyboard.add(button)

        ms_bot.send_message(message.chat.id, "Мы нашли похожую музыку. Выбирай", reply_markup=keyboard)
    else:
        ms_bot.send_message(message.chat.id, "По этому запросу ничего не найдено. Уточни запрос")


@ms_bot.callback_query_handler(func=lambda call: True)
def call_back_handler(call):
    button_key = call.data
    chat_id = call.from_user.id

    try:
        button_value = json.loads((redis_client.get(button_key)).decode('utf-8'))
    except Exception as e:
        print(e)
        return None

    if button_value['type'] == 'suggest':
        generate(data=button_value['data'], chat_id=chat_id)
    else:
        download_send(data=button_value['data'], chat_id=chat_id)


def generate(data, chat_id):
    songs = musicsense_client.helper_generate_songs('track', data['artist'], data['title'], 'track', limit=5)
    keyboard = types.InlineKeyboardMarkup()
    for song in songs['data']['items']:
        text = "{artist}~{title}".format(artist=song['artist'], title=song['title'])
        button_key = str(uid.uuid4())
        call_data = button_key
        button_value = json.dumps({'type': 'generate', 'data': song})
        redis_client.mset({button_key: button_value})
        redis_client.expire(button_key, 86400)
        button = types.InlineKeyboardButton(text=text, callback_data=call_data)
        keyboard.add(button)

    ms_bot.send_message(chat_id, "Похожие песни", reply_markup=keyboard)


def download_send(data, chat_id):
    stream = musicsense_client.musicfeed_stream(data['sound_track_id'])
    artist=data['artist']
    track=data['title']
    album= data['album'] if data['album'] else ''
    ms_bot.send_audio(chat_id,
                            audio=(stream['data']).read(),
                            duration=data['duration'],
                            title="{artist} {track} {album}".format(artist=artist,
                                                                    track=track,
                                                                    album=album),
                            timeout=600)



if __name__ == '__main__':
    ms_bot.polling(none_stop=True)
