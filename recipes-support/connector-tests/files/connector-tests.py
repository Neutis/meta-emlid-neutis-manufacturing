#!/usr/bin/python3

import select
import subprocess

from time import sleep
from systemd import journal

import sys
import alsaaudio

from alsaaudio import (
    PCM_PLAYBACK,
    PCM_CAPTURE,
    PCM_NORMAL,
    PCM_NONBLOCK)


HDMI_CONSOLE = '/dev/tty1'
AUDIO_FILE_PATH = '/tmp/test.wav'


tests_list = [
    ('USB TOP', 'usb 4-1: new high-speed USB device number'),
    ('USB BOTTOM', 'usb 3-1: new high-speed USB device number'),
    ('MicroSD', 'mmc0: new high speed SDHC card'),
    ('Ethernet', 'eth0: Link is Up')
]


def print_hdmi(text):
    with open(HDMI_CONSOLE, 'w') as video_console:
        video_console.write(str(text) + '\n')


class JournalReader:
    def __init__(self):
        self._journal = journal.Reader()
        self._journal.log_level(journal.LOG_INFO)
        self._journal.seek_tail()

        self._p = select.poll()
        self._p.register(self._journal, self._journal.get_events())

    def wait_dev(self, search_str):
        while self._p.poll():
            if self._journal.process() != journal.APPEND:
                continue

            for entry in self._journal:
                if entry['MESSAGE'] != "":
                    if search_str in entry['MESSAGE']:
                        print(entry['MESSAGE'])
                        return


class Audio:
    def __init__(self, audio_file):
        self._audio_file = audio_file
        self._record = alsaaudio.PCM(PCM_CAPTURE, PCM_NONBLOCK, device='default')
        self._play = alsaaudio.PCM(PCM_PLAYBACK, PCM_NORMAL, device='default')
        self._mixer_record = alsaaudio.Mixer(control='Line In', id=0, cardindex=-1, device='default')
        self._mixer_play = alsaaudio.Mixer(control='Line Out', id=0, cardindex=-1, device='default')

    def setup(self):
        # Setup Line In
        self._mixer_record.setvolume(100)
        self._mixer_record.setrec(1)
        self._record.setchannels(1)
        self._record.setrate(44100)
        self._record.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._record.setperiodsize(160)

        # Setup Line Out
        self._mixer_play.setvolume(100)
        self._play.setchannels(1)
        self._play.setrate(44100)
        self._play.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._play.setperiodsize(160)

    def record(self):
        loops = 20000

        f = open(self._audio_file, 'wb')

        while loops > 0:
            loops -= 1
            # Read data from device
            l, data = self._record.read()

            if l:
                f.write(data)
                sleep(.001)

    def play(self):
        f = open(self._audio_file, 'rb')
        data = f.read()
        self._play.write(data)


def run_audio_test():
    try:
        audio = Audio(AUDIO_FILE_PATH)
        audio.setup()
    except Exception as error:
        print_hdmi('ERROR: {}'.format(error))
        return

    while True:
        print_hdmi('LINEIN: start playing music, recording...')

        try:
            audio.record()
        except Exception as error:
            print_hdmi('ERROR: {}'.format(error))
            continue

        print_hdmi('LINEOUT: start listening music, playing...')

        try:
            audio.play()
        except Exception as error:
            print_hdmi('ERROR: {}'.format(error))
            continue

        print_hdmi('The recorded melody was played')

        try:
            subprocess.check_call("rm -f {}".format(AUDIO_FILE_PATH), shell=True)
        except Exception:
            pass

        return


def run_camera_test():
    cam_ret = "FALSE"

    try:
        for i in range(3):
            subprocess.check_call("fswebcam -d /dev/video0 -r 1280x720 /tmp/image.jpg && rm -f /tmp/image.jpg", shell=True)
    except Exception as error:
        print_hdmi(error)
    else:
        cam_ret = "TRUE"

    return cam_ret


def run_tests():
    j = JournalReader()

    # Wait for HDMI connection
    j.wait_dev('fb0:  frame buffer device')
    sleep(3)
    print_hdmi('\nHDMI found')

    for test in tests_list:
        print_hdmi('Insert device into {}'.format(test[0]))
        print_hdmi('Waiting...')
        j.wait_dev(test[1])
        print_hdmi('{}: TRUE'.format(test[0]))

    print_hdmi('DONE!')

    #  Camera test
    print_hdmi('Camera testing...')
    cam_ret = run_camera_test()
    print_hdmi('Camera: {}'.format(cam_ret))
    print_hdmi('DONE!')

    # Audio test
    print_hdmi('Audio testing...')
    run_audio_test()
    print_hdmi('DONE!')


if __name__ == '__main__':
    run_tests()

