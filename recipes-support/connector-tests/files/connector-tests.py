#!/usr/bin/python3

import select
import subprocess

from systemd import journal


HDMI_CONSOLE = '/dev/tty1'


tests_list = [
    ('USB TOP', 'usb 4-1: new high-speed USB device number'),
    ('USB BOTTOM', 'usb 3-1: new high-speed USB device number'),
    ('MicroSD', 'mmc0: new high speed SDHC card'),
    ('Ethernet', 'eth0: Link is Up')
]


def print_hdmi(text):
    with open(HDMI_CONSOLE, 'w') as video_console:
        video_console.write(text+'\n')


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


def run_tests():
    j = JournalReader()

    # Wait for HDMI connection
    j.wait_dev('fb0:  frame buffer device')
    print_hdmi('\nHDMI found')

    for test in tests_list:
        print_hdmi('Insert device into {}'.format(test[0]))
        print_hdmi('Waiting...')
        j.wait_dev(test[1])
        print_hdmi('{}: TRUE'.format(test[0]))

    #  Camera test
    cam_ret = "FALSE"

    print_hdmi('Camera testing...')

    try:
        for i in range(5):
            subprocess.check_call("fswebcam -d /dev/video0 -r 1280x720 /image.jpg && rm -f /image.jpg", shell=True)
    except:
        pass
    else:
        cam_ret = "TRUE"

    print_hdmi('Camera: {}'.format(cam_ret))

    print_hdmi('DONE!')


if __name__ == '__main__':
    run_tests()
