# Copyright (c) 2021 by Phase Advanced Sensor Systems, Inc.
import usb.core

from . import tmc


class DS1104Z(tmc.USB488Device):
    def __init__(self, usb_dev):
        super().__init__(usb_dev)
        self.max_out_size = 64

    def recv_dev_dep_msg_in(self):
        # This device is pretty buggy and sends things in 64-byte chunks even
        # when it has wMaxPacketSize set to 512 (which it magically changes
        # from 64 after receiving the first command... what a mess).  We do
        # larger reads in case some day Rigol fixes their stuff.
        packet = self.bulk_in_ep.read(512)
        hdr    = tmc.DevDepMsgIn.unpack(packet[:tmc.DevDepMsgIn._EXPECTED_SIZE])
        data   = packet[tmc.DevDepMsgIn._EXPECTED_SIZE:]
        while len(data) < hdr.transferSize and len(packet) == 64:
            packet = self.bulk_in_ep.read(512)
            data  += packet
        return hdr, data[:hdr.transferSize]

    def _read_tmc_block(self, cmd_bin):
        # Read the first 16 bytes so we can extract the data length.  The Rigol
        # is super buggy and this kind of works around it.
        hdr, data = self.query_bin(cmd_bin, transferSize=16)
        assert hdr.transferSize == 16
        assert len(data) == 16

        # Extract the total data length from the start of the data section and
        # compute the remaining transfer size.
        assert data[0] == ord('#')
        digits       = int(data[1:2])
        count        = int(data[2:2 + digits])
        transferSize = 2 + digits + count - 16 + 1

        # Request the rest of it.
        self.send_request_dev_dep_msg_in(transferSize=transferSize)
        hdr2, data2 = self.recv_dev_dep_msg_in()
        assert hdr2.transferSize == len(data2)
        assert hdr2.bmTransferAttributes == 1

        # Strip the header and the trailing newline.
        assert data2[-1] == ord('\n')
        hdr    = data[:2 + digits]
        result = data[2 + digits:] + data2[:-1]
        assert len(result) == count
        return hdr, result

    def read_disp_data(self):
        return self._read_tmc_block(b':DISP:DATA?')

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
