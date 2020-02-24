#!/usr/bin/env python3

from datetime import datetime
import logging
import os
import requests
import time

from bluepy.btle import BTLEDisconnectError
from miband import miband

BACKEND_URL = 'http://antonchek.me/heartrater/push'

HOME_PATH = os.getenv('HOME', '~')
CONFIG_DIR = os.path.join(HOME_PATH, '.heartrater')
DEVICE_MAC_ADDRESS_PATH  = os.path.join(CONFIG_DIR, '.device_mac_address')
DEVICE_TOKEN_PATH = os.path.join(CONFIG_DIR, '.device_token')
SERVER_TOKEN_PATH = os.path.join(CONFIG_DIR, '.server_token')

MAC_ADDR = None
with open(DEVICE_MAC_ADDRESS_PATH, 'r') as file_input:
    MAC_ADDR = file_input.read().strip()

AUTH_KEY = None
with open(DEVICE_TOKEN_PATH, 'r') as file_input:
    AUTH_KEY = file_input.read().strip()

SERVER_TOKEN = None
with open(SERVER_TOKEN_PATH, 'r') as file_input:
    SERVER_TOKEN = file_input.read().strip()

_logger_ = logging.getLogger("heartrater_client")
_logger_.setLevel(logging.DEBUG)

log_file_handler = logging.FileHandler(os.path.join(CONFIG_DIR, 'client.log'))
log_file_handler.setLevel(logging.DEBUG)
log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file_handler.setFormatter(formatter)
log_console_handler.setFormatter(formatter)
_logger_.addHandler(log_console_handler)
_logger_.addHandler(log_file_handler)

if 1 < len(MAC_ADDR) != 17:
    _logger_.error('Mac adress is not correct')
    exit(1)

if AUTH_KEY:
    if 1 < len(AUTH_KEY) != 32:
        _logger_.error('Auth key is not correct')
        exit(1)

# Convert Auth Key from hex to byte format
if AUTH_KEY:
    AUTH_KEY = bytes.fromhex(AUTH_KEY)


class HeartRateProcessor:
    def __init__(self, data_file_name):
        self.data_file_name_ = data_file_name

    def process(self, rate):
        _logger_.info('Send rate %d' % rate)
        try:
            requests.get(url=BACKEND_URL, params={
                'timestamp': '%.2f' % time.time(),
                'rate': rate,
                'token': SERVER_TOKEN
            })
        except:
            pass


if __name__ == "__main__":
    heart_rate_processor = HeartRateProcessor('/home/pi/heart_rate.tsv')
    while True:
        try:
            band = miband(MAC_ADDR, AUTH_KEY, debug=True)
            _logger_.info('Start init')
            band.initialize()
            _logger_.info('Finish init')
            band.start_heart_rate_realtime(heart_measure_callback=heart_rate_processor.process)
        except BTLEDisconnectError:
            _logger_.error('Connection to the MIBand failed. Trying out again in 3 seconds')
            time.sleep(3)
            continue
        except KeyboardInterrupt:
            print("\nExit.")
            exit()
        except Exception as exception:
            _logger_.error("Unexpect exception: %s %s" % (type(exception), str(exception)))
            time.sleep(3)
            continue
            
    exit(1)
