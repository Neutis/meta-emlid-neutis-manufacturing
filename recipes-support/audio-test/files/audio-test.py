#!/usr/bin/python3

import sys
import alsaaudio

from time import sleep
from alsaaudio import PCM_PLAYBACK, PCM_CAPTURE, PCM_NORMAL, PCM_NONBLOCK


AUDIO_FILE_PATH = '/tmp/test.wav'


class Audio:
    def __init__(self, audio_file):
        self._audio_file = audio_file
        self._record = alsaaudio.PCM(PCM_CAPTURE, PCM_NONBLOCK, device='default') 
        self._play = alsaaudio.PCM(PCM_PLAYBACK, PCM_NORMAL, device='default')
        self._mixer_record = alsaaudio.Mixer(control='Line In', id=0, cardindex=-1, device='default')
        self._mixer_play = alsaaudio.Mixer(control='Line Out', id=0, cardindex=-1, device='default')

    def setup(self):
        # Setup Line In
        self._mixer_record.setvolume(80)
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


def run_test():
    try:
        audio = Audio(AUDIO_FILE_PATH)
        audio.setup()
    except:
        sys.exit('Audio not available')

    input('Insert cable into LINEIN, start music and press Enter')

    audio.record()

    input('Insert speakers into LINEOUT and press Enter')

    audio.play()

    print('The recorded melody was played')


if __name__ == '__main__':
    run_test()
