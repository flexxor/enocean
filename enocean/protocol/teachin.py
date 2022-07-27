from enocean.communicators import Communicator
from enocean.protocol.constants import PACKET
from enocean.protocol.packet import Packet, RadioPacket

import logging


class TeachInHelper:
    logger = logging.getLogger()

    @staticmethod
    def create_bs4_teach_in_response(cls, packet: Packet, communicator: Communicator) -> RadioPacket:
        # let's create a proper response
        rorg = packet.rorg
        # print("rorg of requesting device: %s" % str(rorg))
        cls.logger.info("rorg of requesting device: %s" % str(rorg))
        func = packet.rorg_func
        cls.logger.info("rorg_func of requesting device: %s" % str(func))
        # print("rorg_func of requesting device: %s" % str(func))
        rorg_type = packet.rorg_type
        cls.logger.info("rorg_type of requesting device: %s" % str(rorg_type))
        # print("rorg_type of requesting device: %s" % str(rorg_type))
        base_id = communicator.base_id

        teach_in_response_packet: RadioPacket = \
            Packet.create(PACKET.RADIO_ERP1,
                          # rorg=RORG.BS4,  # respond with BS4 teach-in-response
                          rorg=rorg,
                          rorg_func=func,
                          rorg_type=rorg_type,
                          sender=base_id,
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
        # maybe use utils to get the next free base_id
        # base_id = self.base_id
        cls.logger.info("base id: {}" % base_id)
        # print("base id: {}" % base_id)
        teach_in_response_packet.sender = base_id

        # build the optional data
        # subTelegram Number + destination + dBm (send case: FF) + security (0)
        optional = [3] + destination + [0xFF, 0]
        teach_in_response_packet.optional = optional
        radio_response_packet = teach_in_response_packet.parse()
        cls.logger.info("BS4 teach-in response created")

        return radio_response_packet

