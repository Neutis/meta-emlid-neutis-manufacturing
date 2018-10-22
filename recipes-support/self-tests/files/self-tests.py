#!/usr/bin/python

# Written by Aleksandr Aleksandrov <aleksandr.aleksandrov@emlid.com>,
# Egor Fedorov <egor.fedorov@emlid.com>
#
# Copyright (c) 2018, Emlid Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
import serial
import logging
import subprocess
import collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERIAL_NUMBER_PATH = "/var/run/serial_number"

wifi_mac_address = None
bt_mac_address = None


def get_serial_number():
    slept = 0
    sleep_step = 0.1
    sleep_max_steps = 1.0

    while True:
        try:
            with open(SERIAL_NUMBER_PATH, "r") as serial_number_file:
                serial_number = serial_number_file.readline()

            logger.debug("Reading serial number: {}".format(serial_number))

            if serial_number:
                return serial_number
        except Exception:
            pass

        if slept >= sleep_max_steps:
            logger.exception("Could not read serial number")
            break

        time.sleep(sleep_step)
        slept += sleep_step

    return ""


def get_qr_code_text(serial_number):
    if not wifi_mac_address or not bt_mac_address:
        return ""

    qr_code_text = "{}({})/{}".format(
        wifi_mac_address,
        bt_mac_address[9:],
        serial_number)

    return qr_code_text


def get_cryptochip_public_key():
    try:
        return subprocess.check_output(["crypto_chip_test", "-p"]), True
    except Exception:
        return "Error", False


def run_self_tests():
    tester = Tester()
    tester.run()
    return tester.to_dict()


def test_crypto_chip():
    _, result = get_cryptochip_public_key()
    return result


def test_wifi():
    global wifi_mac_address

    try:
        wifi_mac_address = subprocess.check_output(
            "ifconfig | grep HWaddr | grep wlan0 | awk '{print $5}'",
            shell=True).strip("\n")
    except Exception as error:
        logger.error(error)

    return bool(wifi_mac_address)


def test_bluetooth():
    global bt_mac_address

    try:
        subprocess.check_output(["hciconfig", "hci0", "up"])
        bt_mac_address = subprocess.check_output(
            "hcitool dev | cut -sf3", shell=True).strip("\n")
    except Exception as error:
        logger.error(error)

    return bool(bt_mac_address)


class SelfTest(object):

    max_attempts = 10
    attempt_step = 0.15

    starting_template = "Running {} test..."
    passed_template = "{} test passed"
    passed_with_attempts_template = "{} test passed after {} attempts"
    failed_template = "{} test failed"

    def __init__(self, name, test=None):
        self.name = name
        self.test_method = test

    def execute(self):
        self.log_start()
        return self.perform_test_attempts()

    def perform_test_attempts(self):
        passed = False
        attempts = self.max_attempts

        while not passed and attempts > 0:
            passed = self.test_method()
            time.sleep(self.attempt_step)
            attempts -= 1

        if passed:
            attempts_made = self.max_attempts - attempts
            self.log_pass(attempts_made=attempts_made)
        else:
            self.log_fail()

        return passed

    def log_start(self):
        logger.info(self.starting_template.format(self.name))

    def log_pass(self, attempts_made=None):
        if attempts_made is None or attempts_made == 1:
            logger.info(self.passed_template.format(self.name))
        else:
            logger.info(self.passed_with_attempts_template.format(
                self.name, attempts_made))

    def log_fail(self):
        logger.critical(self.failed_template.format(self.name))


class Tester(object):

    def __init__(self):
        self.tests = [
            SelfTest("wifi", test_wifi),
            SelfTest("crypto-chip", test_crypto_chip),
            SelfTest("bluetooth", test_bluetooth),
            SelfTest("software", lambda: True)
        ]

        self.results = collections.OrderedDict()

    def run(self):
        for test in self.tests:
            passed = test.execute()
            self.results[test.name] = passed

    def to_dict(self):
        return {
            "test_results_string": self.build_test_results_string(),
            "test_results": self.results
        }

    def build_test_results_string(self):
        s = ",".join(
            "{}:{}".format(name, int(passed)) for name, passed in self.results.iteritems()
        )

        logger.debug("Test results string built:\n{}".format(s))
        return s


def send_to_serial(test_results_string):
    device_serial_number = get_serial_number()
    qr_code_text = get_qr_code_text(device_serial_number)

    begin_mess = "B_R_M"
    end_mess = "E_R_M"
    summary = test_results_string

    if device_serial_number:
        serial_number_key = "serial-number"
    else:
        serial_number_key = "None"

    if qr_code_text:
        qr_code_text_key = "qr-code-text"
    else:
        qr_code_text_key = "None"

    results = "{0}{1};;{2}:{3};;{4}:{5}{6}".format(
        begin_mess,
        summary,
        serial_number_key,
        device_serial_number,
        qr_code_text_key,
        qr_code_text,
        end_mess)

    logger.info("Sending results string to the flasher:\n{}".format(results))
    done = False

    while True:
        try:
            s = serial.Serial(
                "/dev/ttyGS0", baudrate=115200, timeout=0.5, write_timeout=0.5)
        except serial.SerialException as error:
            logger.error(error)
            continue

        try:
            message = ""

            while True:
                message += s.read(512)

                if "poll" in message:
                    break

            message = ""

            while True:
                s.write(results)
                s.flush()
                message += s.read(512)

                if "done" in message:
                    done = True
                    break
        except serial.SerialException as error:
            logger.error(error)

        s.close()

        if done:
            break

    logger.debug("Self-tests: done!")


def main():
    device_info = run_self_tests()
    send_to_serial(device_info["test_results_string"])


if __name__ == "__main__":
    main()
