from enum import IntEnum


class SmartAckCommandCode(IntEnum):
    SA_WR_LEARNMODE = 0x01  # Code 01 - Set/Reset Smart Ack learn mode
    SA_RD_LEARNMODE = 0x02  # Code 02 - Get Smart Ack learn mode state
    SA_WR_LEARNCONFIRM = 0x03  # Used for Smart Ack to add or delete a mailbox of a client
    SA_WR_CLIENTLEARNRQ = 0x04  # Send Smart Ack Learn request (Client)
    SA_WR_RESET = 0x05  # Send reset command to a Smart Ack client
    SA_RD_LEARNEDCLIENTS = 0x06  # Get Smart Ack learned sensors / mailboxes
    SA_WR_RECLAIMS = 0x07  # Set number of reclaim attempts
    SA_WR_POSTMASTER = 0x08  # Activate/Deactivate Post master functionality
