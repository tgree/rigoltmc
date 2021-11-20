# Copyright (c) 2021 by Phase Advanced Sensor Systems, Inc.
import usb.core

from . import tmc

class DS1104Z(tmc.Device):
    def __init__(self, usb_dev):
        super().__init__(usb_dev)

    @staticmethod
    def find_usb_dev(**kwargs):
        return list(usb.core.find(find_all=True, idVendor=0x1AB1,
                                  idProduct=0x04CE))

    @staticmethod
    def find_one_usb_dev(**kwargs):
        usb_devs = DS1104Z.find_usb_dev(**kwargs)
        if len(usb_devs) > 1:
            raise Exception('Multiple matching devices: %s' %
                            ', '.join(ud.serial_number for ud in usb_devs))
        if not usb_devs:
            raise Exception('No matching devices.')
        return usb_devs[0]
