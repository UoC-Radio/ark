#!/usr/bin/env python3
import configparser
import datetime
import errno
import logging
import logging.handlers
import os
import re
import traceback
import subprocess
import sys
import threading
from shutil import which
import argparse

"""
<Code from timeshift/download.py - ported to python 3>
"""
# Original source: https://pypi.python.org/pypi/timeshift
import time
import urllib.request


class TimeLimitElapsed(RuntimeError):
    pass


def download_time_limit(url, filename=None, time_limit=0):
    def callback(count, blocksize, filesize):
        pass

    starttime = time.time()
    if time_limit > 0:
        def callback(count, blocksize, filesize):
            elapsed = time.time() - starttime
            if elapsed > time_limit:
                raise TimeLimitElapsed

    try:
        f = open(filename, 'w')
    except IOError:
        raise IOError('Cannot write to {0}'.format(filename))
    else:
        f.close()

    try:
        urllib.request.urlretrieve(url, filename=filename, reporthook=callback)
    except TimeLimitElapsed:
        pass
"""
</Code from timeshift/download.py - ported to python 3>
"""


class SilenceDetector:
    def __init__(self, stream_url, rec_duration, check_interval, restart_command, logging_path):
        self._stream_url = stream_url
        self._rec_duration = rec_duration
        self._check_interval = check_interval
        self._restart_command = restart_command
        self._logging_path = logging_path
        self._logger = logging.getLogger('SilenceDetector')

        # Folder for the temporary files
        if not os.path.exists(logging_path):
            os.mkdir(logging_path)

        self.initialize_logging(os.path.join(logging_path, 'silence.log'))

    # TODO create logging file as suggested in: https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    def initialize_logging(self, log_filepath):
        self._logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(log_filepath, maxBytes=100000, backupCount=5)
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p'))
        self._logger.addHandler(handler)

    def do_work(self):
        # Download chunk
        filename = 'UOC-{:%Y-%m-%d_%H:%M:%S}.mp3'.format(datetime.datetime.now())
        filepath = os.path.join(self._logging_path, filename)

        try:
            self._logger.debug('Preparing downloading.')
            download_time_limit(self._stream_url, filepath, self._rec_duration)
            self._logger.debug('The file was downloaded.')
        except IOError:
            self._logger.error('IO error while downloading file. Exiting.')
            sys.exit(errno.EIO)
        except:
            self._logger.error('Unexpected error while downloading file. Exiting.')
            self._logger.error(traceback.format_exc())
            sys.exit(1)

        self._logger.debug('Preparing ffmpeg call.')
        cmd = ['ffmpeg', '-i', filepath, '-af', 'silencedetect=n=-60dB:d={}'.
            format(self._rec_duration), '-f', 'null', '-']
        try:
            out = subprocess.check_output(cmd, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=5)
        except subprocess.TimeoutExpired:
            self._logger.error('ffmpeg call timeout. Exiting.')
            sys.exit(errno.EIO)
        except:
            self._logger.error('Unexpected error while calling ffmpeg. Exiting.')
            self._logger.error(traceback.format_exc())
            sys.exit(1)

        self._logger.debug('ffmpeg result received.')

        # We have silence if exactly one silence element (which is always silence_start) is reported.
        # Of course capture length should be reasonable in order to bypass cases of silence between tracks when
        # crossfade is not enabled.
        is_silent = len(re.findall(b'silence_(start|end)', out)) == 1

        # Cleanup
        os.remove(filepath)

        if is_silent:
            out = subprocess.check_output(self._restart_command.split(' '), stdin=subprocess.DEVNULL,
                                          stderr=subprocess.STDOUT, timeout=5)

            if out == b'':
                self._logger.warning('Silence detected. The scheduler was succesfully restarted')
            else:
                self._logger.error('Silence detected. The scheduler was not restarted due to {}'.format(out.decode()))
        else:
            self._logger.info('Stream is in good state')

        # Call the working thread normally every check_interval seconds or 2*check_interval seconds
        # if a restart was required
        threading.Timer(self._check_interval if not is_silent else self._check_interval, self.do_work).start()


def main(args):
    # Locate ffmpeg
    if not which('ffmpeg'):
        sys.exit('ffmpeg executable not found in the system. Please install it through your package manager.')

    # Find if ffmpeg has the required filter
    out = subprocess.check_output(['ffmpeg', '-filters'], stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=5)
    if re.search(b'silencedetect', out) is None:
        sys.exit('Installed ffmpeg version does not provide the required \'silencedetect\' filter.')

    parser = configparser.ConfigParser()

    # Initialize the detector object and start working
    silence_detector = SilenceDetector(args.stream_url, int(args.rec_duration), int(args.check_interval), args.action, args.logging_path)
    silence_detector.do_work()

    # Block the main thread
    while True:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='A silence detector using ffmpeg')
    parser.add_argument('--rec_duration', nargs='?', type=int, default=10,
                        help='The directory which contains the music library.')
    parser.add_argument('--check_interval', nargs='?', type=int, default=30,
                        help='The filepath to store inspection output')
    parser.add_argument('--stream_url', nargs='?', type=str, default='http://rs.radio.uoc.gr:8000/uoc_128.mp3',
                        help='The filepath to store inspection output')
    parser.add_argument('--action', nargs='?', type=str, default='systemctl --user restart audio-scheduler',
                        help='E.g. a command to execute on silence detection')
    parser.add_argument('--logging_path', nargs='?', type=str, default='/tmp/silence_detector',
                        help='Path to store the log')
    args = parser.parse_args()

    main(args)
