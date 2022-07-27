#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from enocean.consolelogger import init_logging
import enocean.utils
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import Packet
from enocean.protocol.constants import PACKET
from enocean.protocol.common_command_codes import CommonCommandCode
from enocean.protocol.smart_ack_command_codes import SmartAckCommandCode
from enocean import utils
import sys
import traceback
import time

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
communicator = SerialCommunicator(port='/dev/ttyUSB0')

packet: Packet = Packet(PACKET.COMMON_COMMAND, [0x03])  # CO_RD_VERSION: Read the device version information

communicator.daemon = True
communicator.start()
# communicator.send(packet)

if communicator.is_alive():
    try:
        receivedPacket = communicator.receive.get(block=True, timeout=1)
        if receivedPacket.packet_type == PACKET.RESPONSE:
            print('Return Code: %s' % utils.to_hex_string(receivedPacket.data[0]))
            print('APP version: %s' % utils.to_hex_string(receivedPacket.data[1:5]))
            print('API version: %s' % utils.to_hex_string(receivedPacket.data[5:9]))
            print('Chip ID: %s' % utils.to_hex_string(receivedPacket.data[9:13]))
            print('Chip Version: %s' % utils.to_hex_string(receivedPacket.data[13:17]))
            print('App Description Version: %s' % utils.to_hex_string(receivedPacket.data[17:]))
            print('App Description Version (ASCII): %s' % str(bytearray(receivedPacket.data[17:])))
    except queue.Empty:
        print('Queue empty')

print('The Base ID of your module is %s.' % enocean.utils.to_hex_string(communicator.base_id))
baseid = communicator.base_id
used_base_ids = [baseid]
next_free_base_id = utils.get_next_free_base_id(baseid, used_base_ids)
used_base_ids.append(next_free_base_id)
n_next_free_base_id = utils.get_next_free_base_id(baseid, used_base_ids)
used_base_ids.append(n_next_free_base_id)

# if communicator.base_id is not None:

# send the packet to read learn mode
# read_learn_mode_packet = Packet(PACKET.COMMON_COMMAND, [CommonCommandCode.CO_RD_LEARNMODE])
# write_learn_mode_packet_enable = Packet(PACKET.COMMON_COMMAND, [CommonCommandCode.CO_WR_LEARNMODE, 0x01, 0x0])
# get_freq_info = Packet(PACKET.COMMON_COMMAND, [0x25])
# read_smartack_learnmode = Packet(PACKET.SMART_ACK_COMMAND, [SmartAckCommandCode.SA_RD_LEARNMODE])

# print("Reading learn mode status...")
# communicator.send(read_learn_mode_packet)
# communicator.send(write_learn_mode_packet_enable)
# communicator.send(get_freq_info)
# communicator.send(read_smartack_learnmode)

last_time = time.localtime()
time_in_seconds = time.time()
print("Time %s" % time.strftime("%H:%M", last_time))

learned_devices = []

# read the answer, check for communicator thread first
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
        # result = communicator.receive.get(block=True, timeout=1)
        if packet.packet_type == PACKET.RESPONSE:
            print('result:')
            print(packet)
            print('Return Code: %s' % utils.to_hex_string(packet.data[0]))
            # TODO: get data from packet (See ESP, 2.5.26)
            # print("Learn mode active (0=no, 1=yes): %s" % utils.to_hex_string(packet.data[1]))
            # optional data
        else:
            if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.BS4:
                # get the third bit of the fourth byte and check for "0".
                if utils.get_bit(packet.data[4], 3) == 0:
                    # we have a teach-in packet
                    # let's create a proper response
                    rorg = packet.rorg
                    print("rorg of requesting device: %s" % str(rorg))
                    func = packet.rorg_func
                    print("rorg_func of requesting device: %s" % str(func))
                    rorg_type = packet.rorg_type
                    print("rorg_type of requesting device: %s" % str(rorg_type))
                    teach_in_response_packet: RadioPacket = Packet.create(PACKET.RADIO_ERP1,
                                                                          #rorg=RORG.BS4,        # respond with BS4 teach-in-response
                                                                          rorg=rorg,
                                                                          #rorg_func=0x20,       # value for thermostat # TODO: read from incoming packet
                                                                          rorg_func=func,
                                                                          #rorg_type=0x01,       # value for thermostat
                                                                          rorg_type=rorg_type,
                                                                          sender=communicator.base_id,
                                                                          learn=True)

                    # copy over the packet data as it will be sent back with slight variation
                    teach_in_response_packet.data[1:5] = packet.data[1:5]

                    # set the bits of the byte for the success case (F0 = 11110000)
                    teach_in_response_packet.data[4] = 0xF0

                    # teach_in_response_packet.destination = packet.
                    # set destination to former sender
                    destination = packet.data[-5:-1]
                    teach_in_response_packet.destination = destination

                    # set sender to base id (no offset)
                    # TODO: test base id + 1
                    base_id = communicator.base_id
                    print("base id: {}" % base_id)
                    teach_in_response_packet.sender = communicator.base_id

                    # build the optional data
                    # subTelegram Number + destination + dBm (send case: FF) + security (0)
                    optional = [3] + destination + [0xFF, 0]
                    teach_in_response_packet.optional = optional
                    teach_in_response_packet.parse()
                    print("response created")

                    # send the packet via the communicator
                    successful_sent = communicator.send(teach_in_response_packet)

                    if successful_sent:
                        # the package was put to the transmit queue
                        print("Sent teach-in response")  # taught in successfully thermostat at 2022-05-08 19:37

                # no BS4-teach-in-packet has arrived
                if packet.data[-5:-1] == [1, 1, 222, 176]:
                    print("data from thermo arrived: %s" % utils.to_hex_string(packet.data))
                    data_response: RadioPacket = Packet.create(PACKET.RADIO_ERP1, rorg=RORG.BS4, rorg_func=0x20,
                                                               rorg_type=0x01,
                                                               sender=communicator.base_id, learn=False)
                    data_response.data[1] = 0x5A            # valve position or temperature set 0x50 = 80
                    # data_response.data[1] = 0x00
                    # data_response.data[2] = 0x0A
                    # data_response.data[2] = 0x00            # temperature actual from RCU
                    data_response.data[2] = 0xB0            # temperature actual from RCU
                    # data_response.data[3] = 0xE1
                    data_response.data[3] = 0x21            # set point normal
                    # data_response.data[3] = 0x23            # set point inverse
                    # data_response.data[4] = 0x08
                    data_response.data[4] = 0x08
                    destination = packet.data[-5:-1]
                    data_response.destination = destination
                    data_response.sender = communicator.base_id
                    optional = [3] + destination + [0xFF, 0]
                    data_response.optional = optional
                    data_response.parse()
                    print("data response created")
                    successful_sent = communicator.send(data_response)
                    if successful_sent:
                        print("Sent data response packet")

    except queue.Empty:
        print('Queue empty')
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc(file=sys.stdout)
        break

    # print('Sending example package.')
    # communicator.send(assemble_radio_packet(communicator.base_id))


# endless loop receiving radio packets
# while communicator.is_alive():
#     try:
#         # Loop to empty the queue...
#         packet = communicator.receive.get(block=True, timeout=1)
#         if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.VLD:
#             packet.select_eep(0x05, 0x00)
#             packet.parse_eep()
#             for k in packet.parsed:
#                 print('%s: %s' % (k, packet.parsed[k]))
#         if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.BS4:
#             # parse packet with given FUNC and TYPE
#             for k in packet.parse_eep(0x02, 0x05):
#                 print('%s: %s' % (k, packet.parsed[k]))
#         if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.BS1:
#             # alternatively you can select FUNC and TYPE explicitely
#             packet.select_eep(0x00, 0x01)
#             # parse it
#             packet.parse_eep()
#             for k in packet.parsed:
#                 print('%s: %s' % (k, packet.parsed[k]))
#         if packet.packet_type == PACKET.RADIO_ERP1 and packet.rorg == RORG.RPS:
#             for k in packet.parse_eep(0x02, 0x02):
#                 print('%s: %s' % (k, packet.parsed[k]))
#     except queue.Empty:
#         continue
#     except KeyboardInterrupt:
#         break
#     except Exception:
#         traceback.print_exc(file=sys.stdout)
#         break

if communicator.is_alive():
    communicator.stop()
