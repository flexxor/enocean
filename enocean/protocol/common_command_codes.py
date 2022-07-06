from enum import IntEnum


class CommonCommandCode(IntEnum):
    CO_WR_SLEEP = 0x1  # Code 01 - Enter energy saving mode
    CO_WR_RESET = 0x2  # Code 02 - Reset the device
    CO_RD_VERSION = 0x3  # Code 03 - Read the device version information
    CO_RD_SYS_LOG = 0x4  # Code 04 - Read system log
    CO_WR_SYS_LOG = 0x5  # Code 05 - Reset system log
    CO_WR_BIST = 0x6  # Code 06 - Perform Self Test
    CO_WR_IDBASE = 0x7  # Code 07 - Set ID range base address
    CO_RD_IDBASE = 0x8  # Code 08 - Read ID range base address
    CO_WR_REPEATER = 0x9  # Code 09 - Set Repeater Level
    CO_RD_REPEATER = 0xA  # Code 10 - Read Repeater Level
    CO_WR_FILTER_ADD = 0xB  # Code 11 - Add filter to list
    CO_WR_FILTER_DEL = 0xC  # Code 12 - Delete a specific filter from list
    CO_WR_FILTER_DEL_ALL = 0xD  # Code 13 - Delete all filters from filter list
    CO_WR_FILTER_ENABLE = 0xE  # Code 14 - Enable / Disable filter list
    CO_RD_FILTER = 0xF  # Code 15 - Read filters from filter list
    CO_WR_WAIT_MATURITY = 0x10  # Code 16 - Wait until the end of telegram maturity time before received radio telegrams
    # will be forwarded to the external host
    CO_WR_SUBTEL = 0x11  # Code 17 - Enable / Disable transmission of additional subtelegram info to the external host
    CO_WR_MEM = 0x12  # Code 18 - Write data to device memory
    CO_RD_MEM = 0x13  # Code 19 - Read data from device memory
    CO_RD_MEM_ADDRESS = 0x14  # Code 20 - Read address and length of the configuration area and the Smart Ack Table
    CO_RD_SECURITY = 0x15  # Code 21 -  DEPRECATED Read own security information (level, key)
    CO_WR_SECURITY = 0x16  # Code 22 - DEPRECATED Write own security information (level, key)
    CO_WR_LEARNMODE = 0x17  # Code 23 - Enable / disable learn mode
    CO_RD_LEARNMODE = 0x18  # Code 24 - Read learn mode status
    # TODO: up until Code 65
