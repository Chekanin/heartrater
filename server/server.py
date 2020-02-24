#!/usr/bin/env python3

from datetime import datetime
import collections
import io
import logging
import os
import time

from flask import Flask, request, Response
import matplotlib
import matplotlib.pyplot
import matplotlib.dates


PORT = os.getenv("HEARTRATER_SERVER_PORT", 80)
HOME_PATH = os.getenv('HOME', '~')
CONFIG_DIR = os.path.join(HOME_PATH, '.heartrater')
STATIC_FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
TOKEN_PATH = os.path.join(CONFIG_DIR, '.server_token')
PUSH_RATE_URL_PATH = "/heartrater/push"
PLOT_IMAGE_URL_PATH = "/heartrater/plot.png"
LOGO_IMAGE_URL_PATH = "/heartrater/logo.jpeg"
LOGO_IMAGE_FILE_PATH = os.path.join(STATIC_FILES_DIR, 'logo.jpeg')
BUFFER_SIZE = 360
PANIC_THRESHOLD = 20
FONT_CONFIG = {
    #  'family' : 'normal',
    'weight' : 500,
    'size'   : 28
}
matplotlib.rc('font', **FONT_CONFIG)

TOKEN = None
with open(TOKEN_PATH, 'r') as file_input:
    TOKEN = file_input.read().strip()

_logger_ = logging.getLogger("heartrater_server")
_logger_.setLevel(logging.DEBUG)

log_file_handler = logging.FileHandler(os.path.join(CONFIG_DIR, 'server.log'))
log_file_handler.setLevel(logging.DEBUG)
log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file_handler.setFormatter(formatter)
log_console_handler.setFormatter(formatter)
_logger_.addHandler(log_console_handler)
_logger_.addHandler(log_file_handler)

app = Flask(__name__)

StampedRate = collections.namedtuple('StampedRate', [
    'timestamp',
    'rate'
])

class HeartRateProcessor:
    def __init__(self):
        self.buffer_ = collections.deque(maxlen=BUFFER_SIZE)

    def push(self, timestamp, rate):
        _logger_.debug('Push: timestamp=%.2f, rate=%d' % (timestamp, rate))

        stamped_rate = StampedRate(timestamp=timestamp, rate=rate)
        self.buffer_.append(stamped_rate)

        self.check_panic_()

    def build_plot_image_data(self):
        result = io.BytesIO()

        filtered_measurements = list(filter(lambda r: r.rate != 0, self.buffer_))
        if len(filtered_measurements) == 0:
            return result

        x_coordinates = list(map(lambda r: datetime.fromtimestamp(r.timestamp),
                                 filtered_measurements))
        y_coordinates = list(map(lambda r: r.rate, filtered_measurements))

        figure, axes = matplotlib.pyplot.subplots(figsize=(7.0, 7.0))
        axes.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
        axes.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, pos: '%d' % round(x)))
        axes.xaxis.set_major_locator(matplotlib.pyplot.MaxNLocator(4))
        axes.yaxis.set_major_locator(matplotlib.pyplot.MaxNLocator(4))
        axes.plot(x_coordinates, y_coordinates)

        result = io.BytesIO()
        figure.savefig(result, format='png')
        result.seek(0)

        return result

    def check_panic_(self):
        if len(self.buffer_) < PANIC_THRESHOLD:
            return

        for i in range(len(self.buffer_) - PANIC_THRESHOLD, len(self.buffer_)):
            if self.buffer_[i].rate != 0:
                return

        self.send_panic_()

    def send_panic_(self):
        _logger_.warn("Panic!")

processor = HeartRateProcessor()


@app.route(PUSH_RATE_URL_PATH, methods=['GET'])
def incoming():
    _logger_.debug("Push rate: {0}".format(request))

    if request.args.get('token') != TOKEN:
        return Response(status=403)
    timestamp = request.args.get('timestamp')
    rate = request.args.get('rate')
    if timestamp is None or rate is None or not rate.isdigit():
        return Response(status=403)

    processor.push(timestamp=float(timestamp), rate=int(rate))

    return Response(status=200)


@app.route(PLOT_IMAGE_URL_PATH)
def get_plot_image():
    _logger_.debug("Request image: {0}".format(request))

    if request.args.get('token') != TOKEN:
        return Response(status=403)

    image_data = processor.build_plot_image_data()

    return Response(image_data, mimetype='image/png')

@app.route(LOGO_IMAGE_URL_PATH)
def get_logo_image():
    with open(LOGO_IMAGE_FILE_PATH, 'rb') as image:
        return Response(io.BytesIO(image.read()), mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=False)
