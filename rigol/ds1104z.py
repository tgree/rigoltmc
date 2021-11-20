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
        # Read the first 2 bytes to get the number of digits.
        hdr, data = self.query_bin(cmd_bin, transferSize=2)
        assert hdr.transferSize == 2
        assert len(data) == 2

        # Extract the number of digits in the length word and then request it.
        assert data[0] == ord('#')
        digits = int(data[1:])
        self.send_request_dev_dep_msg_in(transferSize=digits)
        hdr2, data2 = self.recv_dev_dep_msg_in()
        assert hdr2.transferSize == len(data2)
        assert len(data2) == digits
        count = int(data2)

        # Request the rest of the block plus the trailing newline.
        self.send_request_dev_dep_msg_in(transferSize=count + 1)
        hdr3, data3 = self.recv_dev_dep_msg_in()
        assert hdr3.transferSize == len(data3)
        assert hdr3.bmTransferAttributes == 1
        assert len(data3) == count + 1

        # Return the final result, stripping the trailing newline.
        assert data3[-1] == ord('\n')
        return data + data2, data3[:-1]

    def read_disp_data(self):
        return self._read_tmc_block(b':DISP:DATA?')

    def read_error(self):
        hdr, data   = self.exec(':SYST:ERR?')
        data        = data.strip()
        err, _, msg = data.partition(',')
        assert msg[0] == msg[-1] == '"'
        return int(err), msg[1:-1]

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
