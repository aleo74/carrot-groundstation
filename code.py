import time
import struct
import board
import busio
import digitalio
import json

# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24

# invalid default values for scoping
SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)

# using board.SPI() automatically selects the MCU's
# available SPI pins, board.SCK, board.MOSI, board.MISO
ce = digitalio.DigitalInOut(board.GP14)
csn = digitalio.DigitalInOut(board.GP17)
# spi = board.SPI() # init spi bus object
spi = busio.SPI(clock=board.GP6, MOSI=board.GP7, MISO=board.GP4)

# initialize the nRF24L01 on the spi bus object
nrf = RF24(spi, csn, ce)
# On Linux, csn value is a bit coded
#                 0 = bus 0, CE0  # SPI bus 0 is enabled by default
#                10 = bus 1, CE0  # enable SPI bus 2 prior to running this
#                21 = bus 2, CE1  # enable SPI bus 1 prior to running this

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity
nrf.pa_level = -12

# addresses needs to be in a buffer protocol object (bytearray)
address = [b"1Node", b"2Node"]

# to use different addresses on a pair of radios, we need a variable to
# uniquely identify which address this radio will use to transmit
# 0 uses address[0] to transmit, 1 uses address[1] to transmit
radio_number = bool(
    1
)

# set TX address of RX node into the TX pipe
nrf.open_tx_pipe(address[radio_number])  # always uses pipe 0

# set RX address of TX node into an RX pipe
nrf.open_rx_pipe(1, address[not radio_number])  # using pipe 1

# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
payload = [0.0]

# uncomment the following 3 lines for compatibility with TMRh20 library
# nrf.allow_ask_no_ack = False
# nrf.dynamic_payloads = False
# nrf.payload_length = 4

counter = [0]

"""Prints the received value and sends an ACK payload"""

# setup the first transmission's ACK payload
# add b"\0" as a c-string NULL terminating char
buffer = b"World \0" + bytes([counter[0]])
# we must set the ACK payload data and corresponding
# pipe number [0, 5]. We'll be acknowledging pipe 1
nrf.load_ack(buffer, 1)  # load ACK for first response


def listen():
    nrf.listen = True  # put radio into RX mode, power it up
    start = time.monotonic()  # start timer
    my_string = ''
    buffer = b"World \0" + bytes([counter[0]])
    # we must set the ACK payload data and corresponding
    # pipe number [0, 5]. We'll be acknowledging pipe 1
    nrf.load_ack(buffer, 1)  # load ACK for first response
    while (time.monotonic() - start) < 1:
        if nrf.available():
            length, pipe_number = (nrf.any(), nrf.pipe)
            received = nrf.read()
            if length >= 32:
                my_string = my_string + received.decode("utf-8")
            else:
                my_string = my_string + received.decode("utf-8")
                print(my_string)
                try:
                    json.loads(my_string)
                # print(my_string)
                except ValueError:
                    pass
                my_string = ''

            start = time.monotonic()  # reset timer

        buffer = b"" + json.dumps({'Servo': 'deploy'})  # build new ACK
        nrf.load_ack(buffer, 1)  # load ACK for next response

    # send()

    # recommended behavior is to keep in TX mode while idle
    nrf.listen = False  # put radio in TX mode
    nrf.flush_tx()  # flush any ACK payloads that remain

    print('time out...')


while 1:
    listen()
