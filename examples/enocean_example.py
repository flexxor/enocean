#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import time

from enocean.consolelogger import init_logging
import enocean.utils
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import PACKET, RORG
import sys
import traceback

try:
    import queue
except ImportError:
    import Queue as queue


def assemble_radio_packet(transmitter_id):
    return RadioPacket.create(rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01,
                              sender=transmitter_id,
                              CV=50,
                              TMP=21.5,
                              ES='true')


init_logging()
communicator = SerialCommunicator(port="/dev/ttyUSB0")
communicator.start()
print('The Base ID of your module is %s.' % enocean.utils.to_hex_string(communicator.base_id))

# if communicator.base_id is not None:
    # print('Sending example package.')
    # communicator.send(assemble_radio_packet(communicator.base_id))

last_time = time.localtime()
time_in_seconds = time.time()
print("Time %s" % time.strftime("%H:%M", last_time))
# print(last_time.tm_sec)

# endless loop receiving radio packets
while communicator.is_alive():
    current_time = time.time()
    # if current_time > time.localtime(last_time.tm_sec):
    if current_time > time_in_seconds + 5:
        # print(last_time.tm_sec)
        time_in_seconds = current_time
        print("Communicator is still alive ...%s" % time.strftime("%H:%M:%S", time.localtime(current_time)))

    try:
        # Loop to empty the queue...
        packet = communicator.receive.get(block=True, timeout=1)
        if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.VLD:
            packet.select_eep(0x05, 0x00)  # check this
            packet.parse_eep()
            for k in packet.parsed:
                print('%s: %s' % (k, packet.parsed[k]))
        if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.BS4:
            # parse packet with given FUNC and TYPE
            for k in packet.parse_eep(0x02, 0x05):
                print('%s: %s' % (k, packet.parsed[k]))
        if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.BS1:
            # alternatively you can select FUNC and TYPE explicitely
            packet.select_eep(0x00, 0x01)                      # FUNC of window / door contact (FTKE): 00, TYPE: 01
            # parse it
            packet.parse_eep()
            for k in packet.parsed:
                print('%s: %s' % (k, packet.parsed[k]))
        if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.RPS:
            # for k in packet.parse_eep(0x02, 0x02):
            for k in packet.parse_eep(0x10, 0x00):          # FUNC of window handle: 10, TYPE pof window handle: 00
                print('%s: %s' % (k, packet.parsed[k]))
    except queue.Empty:
        continue
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc(file=sys.stdout)
        break

if communicator.is_alive():
    communicator.stop()
