# -*- encoding: utf-8 -*-
from __future__ import print_function, unicode_literals, division, absolute_import

import unittest

from enocean.communicators import Communicator
from enocean.protocol.packet import Packet
from enocean.protocol.constants import RORG, DB6
from enocean.decorators import timing


class TestTeachIns(unittest.TestCase):

    @timing(rounds=100, limit=750)
    def test_ute_in(self):
        communicator = Communicator()
        communicator.base_id = [0xDE, 0xAD, 0xBE, 0xEF]  # 222, 173, 190, 239

        status, buf, packet = Packet.parse_msg(
            bytearray([
                0x55,  # sync byte
                0x00, 0x0D,  # data length: 13 bytes
                0x07,  # Optional length (7 fields fixed for ERP1)
                0x01,  # Packet Type: Radio ERP1
                0xFD,  # CRC8 for header (checked)         1
                0xD4,  # RORG for Universal Teach-In       2
                0xA0,  # DB6 Bin: 1010 0000 --> 1=Bidirectional, 0=Response expected, 10=Teach-in or deletion of
                # Teach-in, 0000=Teach-in query
                0xFF,  # DB5 Bin: 1111 1111 --> FF=Teach-in of all channels is supported by the device
                0x3E,  # DB4 Bin: 0011 1110 --> Manufacturer-ID (8 LSB): 3E
                0x00,  # DB3 Bin: 0000 0000 --> 24-28: not used, 000=Manufacturer-ID (3 MSB)
                0x01,  # DB2 Bin: 0000 0001 --> TYPE of EEP: 0x01
                0x01,  # DB1 Bin: 0000 0001 --> FUNC of EEP: 0x01
                0xD2,  # DB0 Bin: 1101 0010 --> RORG of EEP: 0xD2 (VLD)
                0x01, 0x94, 0xE3, 0xB9,  # Sender ID                         10-13
                0x00,  # Status
                0x01,  # Optional data: number of subtelegram (send: 3 / receive: 0)
                0xFF, 0xFF, 0xFF, 0xFF,  # Broadcast 4 bytes: FF FF FF FF
                0x40,  # dBm: send case: should be FF
                0x00,  # Security level: telegram not processed
                0xAB  # CRC8 for data (checked)
            ])
        )

        assert packet.sender_hex == '01:94:E3:B9'
        assert packet.unidirectional is False
        assert packet.bidirectional is True
        assert packet.response_expected is True
        assert packet.number_of_channels == 0xFF
        assert packet.rorg_manufacturer == 0x3E
        assert packet.rorg_of_eep == RORG.VLD
        assert packet.rorg_func == 0x01
        assert packet.rorg_type == 0x01
        assert packet.teach_in is True
        assert packet.delete is False
        assert packet.learn is True
        assert packet.contains_eep is True

        response_packet = packet.create_response_packet(communicator.base_id)
        assert response_packet.sender_hex == 'DE:AD:BE:EF'
        assert response_packet.destination_hex == '01:94:E3:B9'
        assert response_packet._bit_data[DB6.BIT_7] is True  # Bidirectional
        assert response_packet._bit_data[DB6.BIT_5:DB6.BIT_3] == [False, True]  # 01=Request accepted,
        # teach-in successful
        assert response_packet.data[2:7] == packet.data[2:7]

    def test_4bs_teach_in_var3(self):
        communicator = Communicator()
        communicator.base_id = [0xDE, 0xAD, 0xBE, 0xEF]  # 222, 173, 190, 239

        status, buf, packet = Packet.parse_msg(
            bytearray([
                0x55,  # sync byte
                0x00, 0x0A,  # data length: 10 bytes
                0x07,  # Optional length (7 fields fixed for ERP1)
                0x01,  # Packet Type: Radio ERP1
                0xEB,  # CRC8 for header (checked)          1
                0xA5,  # RORG for 4BS Teach-In              2
                0x04,  # DB3 to DB_1: 6-bit FUNC, 7-bit TYPE, 11-bit Manufacturer ID (24bit, 3 bytes): 0000 0100
                0x0C,  # DB2 Bin: 00001  100
                0x3E,  # DB1 Bin: 0011 1110
                0xE0,  # DB0 Bin: 1110 0000 --> LRN_TYPE: 1=telegram with EEP and manu,
                # EEP_RESULT=x, LRN_RESULT=x, LRN_STATUS: 0=Query, LRN_BIT: 0=Teach-in telegram, xxx
                0x01, 0x94, 0xE3, 0xB9,  # Sender ID                         10-13
                0x00,  # Status
                0x01,  # Optional data: number of subtelegram (send: 3 / receive: 0)
                0xFF, 0xFF, 0xFF, 0xFF,  # Broadcast 4 bytes: FF FF FF FF
                0x40,  # dBm: send case: should be FF
                0x00,  # Security level: telegram not processed
                0x54
                #  0x5E  # CRC8 for data (checked)
            ])
        )

        assert packet.sender_hex == '01:94:E3:B9'
        assert packet.rorg == RORG.BS4
        assert packet.learn is True  # (LRN Status: Query)
        assert packet.contains_eep is True

        assert packet.rorg_func == 0x1
        assert packet.rorg_type == 0x01

        # assert packet.bidirectional is True  #  packet has no attribute bidirectional
        # assert packet.response_expected is True
        assert packet.rorg_manufacturer == 0x43E

        #  assert packet.teach_in is True  # TODO
        #  assert packet.delete is False
        assert packet.contains_eep is True

        response_packet = packet.create_response_packet(communicator.base_id)
        assert response_packet.sender_hex == 'DE:AD:BE:EF'
        #  assert response_packet.
        assert response_packet.destination_hex == '01:94:E3:B9'             # TODO
        assert response_packet._bit_data[DB6.BIT_7] is True  # Bidirectional  # TODO
        assert response_packet._bit_data[DB6.BIT_5:DB6.BIT_3] == [False, True]  # 01=Request accepted,
        # teach-in successful
        assert response_packet.data[2:7] == packet.data[2:7]


if __name__ == '__main__':
    unittest.main()
