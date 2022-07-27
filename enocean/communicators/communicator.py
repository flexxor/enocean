# -*- encoding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import
import logging
import datetime

import threading

from enocean import utils
from enocean.protocol import teachin

try:
    import queue
except ImportError:
    import Queue as queue
from enocean.protocol.packet import Packet, UTETeachInPacket, RadioPacket
from enocean.protocol.constants import PACKET, PARSE_RESULT, RETURN_CODE, RORG
from enocean.protocol.common_command_codes import CommonCommandCode


class Communicator(threading.Thread):
    """
    Communicator base-class for EnOcean.
    Not to be used directly, only serves as base class for SerialCommunicator etc.
    """
    logger = logging.getLogger('enocean.communicators.Communicator')

    def __init__(self, callback=None, teach_in=True):
        super(Communicator, self).__init__()
        # Create an event to stop the thread
        self._stop_flag = threading.Event()
        # Input buffer
        self._buffer = []
        # Setup packet queues
        self.transmit = queue.Queue()
        self.receive = queue.Queue()
        # Set the callback method
        self.__callback = callback
        # Internal variable for the Base ID of the module.
        self._base_id = None
        # Should new messages be learned automatically? Defaults to True.
        # Not sure if we should use CO_WR_LEARNMODE??
        # CO_WR_LEARNMODE is not supported by every device. The e.g. USB 300 does not support this command.

        # create an event to control whether teach-in is enabled (set (true) / clear (false))
        self._teach_in_flag = threading.Event()
        self.teach_in = teach_in

    def _get_from_send_queue(self):
        """ Get message from send queue, if one exists """
        try:
            packet = self.transmit.get(block=False)
            self.logger.info('Sending packet')
            self.logger.debug(packet)
            return packet
        except queue.Empty:
            pass
        return None

    def send(self, packet):
        if not isinstance(packet, Packet):
            self.logger.error('Object to send must be an instance of Packet')
            return False
        self.transmit.put(packet)
        return True

    def stop(self):
        self._stop_flag.set()

    def deactivate_teach_in(self):
        self.logger.info("Teach-in DISABLED")
        self._teach_in_flag.clear()

    def activate_teach_in(self):
        self.logger.info("Teach-in ENABLED")
        self._teach_in_flag.set()

    def parse(self):
        """ Parses messages and puts them to receive queue """
        # Loop while we get new messages
        while True:
            status, self._buffer, packet = Packet.parse_msg(self._buffer)
            # If message is incomplete -> break the loop
            if status == PARSE_RESULT.INCOMPLETE:
                return status

            # If message is OK, add it to receive queue or send to the callback method
            if status == PARSE_RESULT.OK and packet:
                packet.received = datetime.datetime.now()

                if isinstance(packet, UTETeachInPacket) and self.teach_in:
                    response_packet = packet.create_response_packet(self.base_id)
                    self.logger.info('Sending response to UTE teach-in.')
                    self.send(response_packet)

                # TODO: teach-in handling for other RORGS
                if isinstance(packet, RadioPacket) \
                        and packet.packet_type == PACKET.RADIO_ERP1 \
                        and packet.rorg == RORG.BS4:
                    # check for teach in packet AND
                    # TODO: refactor this
                    if self._teach_in_flag is True and utils.get_bit(packet.data[4], 3) == 0:
                        # if self.teach_in is True and utils.get_bit(packet.data[4], 3) == 0:
                        # we have a BS4 teach-in packet AND we want to teach-in the new device
                        # remove print statements
                        # TODO: extract necessary and optional data like eep, sender_id
                        # packet.sender
                        # if packet.contains_eep:
                        teach_in_response_packet = teachin.create_bs4_teach_in_response(packet, self)

                        self.logger.info("BS4 teach-in response created")

                        # send the packet
                        # TODO: send here already? What about callback function
                        successful_sent = self.send(teach_in_response_packet)

                        if successful_sent:
                            # the package was put to the transmit queue
                            self.logger.info("Sent teach-in response")
                            # print("Sent teach-in response")
                        # TODO: here

                if self.__callback is None:
                    self.receive.put(packet)
                else:
                    # TODO: maybe extract data in callback
                    self.__callback(packet)
                self.logger.debug(packet)

    @property  # getter
    def callback(self):
        return self.__callback

    @callback.setter
    def callback(self, callback):
        self.__callback = callback

    @property
    def base_id(self):
        """ Fetches Base ID from the transmitter, if required, otherwise returns the currently set Base ID. """
        # If base id is already set, return it.
        if self._base_id is not None:
            return self._base_id

        # Send COMMON_COMMAND 0x08, CO_RD_IDBASE request to the module
        # self.send(Packet(PACKET.COMMON_COMMAND, data=[0x08]))  # the next line does the same
        self.send(Packet(PACKET.COMMON_COMMAND, data=[CommonCommandCode.CO_RD_IDBASE]))
        # Loop over 10 times, to make sure we catch the response.
        # Thanks to timeout, shouldn't take more than a second.
        # Unfortunately, all other messages received during this time are ignored.
        for i in range(0, 10):
            try:
                packet = self.receive.get(block=True, timeout=0.1)
                # We're only interested in responses to the request in question.
                if packet.packet_type == PACKET.RESPONSE and packet.response == RETURN_CODE.OK and len(packet.response_data) == 4:  # noqa: E501
                    # Base ID is set in the response data.
                    self._base_id = packet.response_data
                    # Put packet back to the Queue, so the user can also react to it if required...
                    self.receive.put(packet)
                    break
                # Put other packets back to the Queue.
                self.receive.put(packet)
            except queue.Empty:
                continue
        # Return the current Base ID (might be None).
        return self._base_id

    @base_id.setter
    def base_id(self, base_id):
        """ Sets the Base ID manually, only for testing purposes. """
        self._base_id = base_id
