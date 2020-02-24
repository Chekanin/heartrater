#!/usr/bin/env python3

import logging
import os
import sched
import threading
import time

from flask import Flask, request, Response
from pyngrok import ngrok
from viberbot import Api
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.picture_message import PictureMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest


PORT = os.getenv('HEARTRATE_VIBER_PORT', 9090)
HOME_PATH = os.getenv('HOME', '~')
CONFIG_DIR = os.path.join(HOME_PATH, '.heartrater')
TOKEN_PATH = os.path.join(CONFIG_DIR, '.viber_token')
SERVER_TOKEN_PATH = os.path.join(CONFIG_DIR, '.server_token')
LOGO_URL = 'http://antonchek.me/heartrater/logo.jpeg'

TOKEN = None
with open(TOKEN_PATH, 'r') as file_input:
    TOKEN = file_input.read().strip()

SERVER_TOKEN = None
with open(SERVER_TOKEN_PATH, 'r') as file_input:
    SERVER_TOKEN = file_input.read().strip()

PLOT_IMAGE_URL = 'http://antonchek.me/heartrater/plot.png?token=%s' % SERVER_TOKEN

_logger_ = logging.getLogger("heartrater_server")
_logger_.setLevel(logging.DEBUG)

log_file_handler = logging.FileHandler(os.path.join(CONFIG_DIR, 'viber_bot.log'))
log_file_handler.setLevel(logging.DEBUG)
log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file_handler.setFormatter(formatter)
log_console_handler.setFormatter(formatter)
_logger_.addHandler(log_console_handler)
_logger_.addHandler(log_file_handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='heartrate',
    auth_token=TOKEN,
    avatar=LOGO_URL  # required argument
))

@app.route('/', methods=['POST'])
def incoming():
    _logger_.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data().decode('utf8'))
    #  logger.debug("Viber request: {0} viber_user: {1}, viber_user_id: ".format(
        #  viber_request, viber_request.get_user, viber_request.get_user.id))

    if isinstance(viber_request, ViberMessageRequest):
        #  message = viber_request.message
        message = PictureMessage(media=PLOT_IMAGE_URL)
            #  text="Viber logo")
        viber.send_messages(viber_request.sender.id, [
            message
        ])
    elif isinstance(viber_request, ViberConversationStartedRequest) \
            or isinstance(viber_request, ViberSubscribedRequest) \
            or isinstance(viber_request, ViberUnsubscribedRequest):
        viber.send_messages(viber_request.sender.id, [
            TextMessage(None, None, viber_request.get_event_type())
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        _logger_.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

def set_webhook(viber):
    public_url = ngrok.connect(port=PORT, proto='http', options={'bind_tls': True})
    viber.set_webhook(public_url)

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    app.run(host='0.0.0.0', port=PORT, debug=True)
