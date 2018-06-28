#!/usr/bin/python

#  Copyright (C) Emlid Limited - All Rights Reserved
#  All information contained in this file is the property of Emlid Limited.
#  The intellectual and technical concepts contained herein are proprietary to
#  Emlid Limited and are protected by copyright law. Distribution of this
#  information or reproduction of this material is strictly forbidden without
#  written permission obtained from Emlid Limited.
#  Written by Aleksandr Aleksandrov <aleksandr.aleksandrov@emlid.com>,
#  Egor Fedorov <egor.fedorov@emlid.com>, 2018

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
    try:
        with open(SERIAL_NUMBER_PATH, "r") as serial_number_file:
            serial_number = serial_number_file.readline()

        logger.debug("Reading serial number: {}".format(serial_number))
        return serial_number
    except IOError:
        logger.exception("Could not read serial number")
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

    slept = 0
    sleep_step = 0.25
    sleep_max_steps = 3 * (1.0 / sleep_step)

    logger.debug("Waiting for bluetooth.target")

    while True:
        try:
            bt_mac_address = subprocess.check_output(
                "hcitool dev | cut -sf3", shell=True).strip("\n")
            if bool(bt_mac_address):
                break
        except Exception:
            pass

        if slept >= sleep_max_steps:
            logger.error("Timed out waiting for bluetooth device")
            return False

        time.sleep(sleep_step)
        slept += sleep_step

    return bool(bt_mac_address)


class SelfTest(object):

    max_attempts = 3

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

    results = "{0}{1};;serial-number:{2};;qr-code-text:{3}{4}".format(
        begin_mess,
        summary,
        device_serial_number,
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

    print(device_info)

    send_to_serial(device_info["test_results_string"])


if __name__ == "__main__":
    main()
