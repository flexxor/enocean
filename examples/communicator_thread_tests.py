import logging.handlers
import queue
import sys
import traceback

from enocean import utils
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import Packet, RadioPacket

a = logging.getLogger()
a.setLevel(logging.INFO)   # set root's level
a.addHandler(logging.StreamHandler())


def assemble_radio_packet(transmitter_id):
    return RadioPacket.create(rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01,
                              sender=transmitter_id,
                              CV=50,
                              TMP=21.5,
                              ES='true')


def callback_function(packet: Packet):
    print("callback function called")
    print("Packet type: %s" % str(packet.packet_type))


def callback_function2(packet: Packet):
    print("Callback function 2 got called")
    print("Packet type: %s" % str(packet.packet_type))


communicator = SerialCommunicator(port=u'/dev/ttyUSB0', callback=callback_function)

communicator.daemon = True  # set behaviour of thread (communicator is deriving from threading.Thread)
communicator.start()

# can we get the callback while thread is running already?
cb = communicator.callback
communicator.send(assemble_radio_packet(communicator.base_id))
# can we set a new callback function while the thread is already running?
communicator.callback = callback_function2
communicator.send(assemble_radio_packet(communicator.base_id))
# can we restore the old callback function?
communicator.callback = callback_function
communicator.send(assemble_radio_packet(communicator.base_id))

communicator.deactivate_teach_in()

communicator.activate_teach_in()


count_queue_empty = 0
while communicator.is_alive() and count_queue_empty < 10:
    try:
        # there are no packets in the receive-queue since we passed a callback function. The queue is always empty
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
        count_queue_empty += 1
        continue
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc(file=sys.stdout)
        break

print("Queue was empty %d times" % count_queue_empty)  # takes about 10 seconds because the get-Operation has a timeout
# of 1 second
if communicator.is_alive():
    communicator.stop()


