#!/usr/bin/python3

import select
from systemd import journal


HDMI_CONSOLE = '/dev/tty1'


tests_list = {
    'USB TOP': 'usb 4-1: new full-speed USB device number',
    'USB BOTTOM': 'usb 3-1: new full-speed USB device number',
    'MicroSD': 'mmc0: new high speed SDHC card',
    'Ethernet': 'eth0: Link is Up'
    }


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

    for name, search_str in tests_list.items():
        print_hdmi('Insert device into {}'.format(name))
        print_hdmi('Waiting...')
        j.wait_dev(search_str)
        print_hdmi('{}: OK'.format(name))

    print_hdmi('All tests passed')


if __name__ == '__main__':
    run_tests()
