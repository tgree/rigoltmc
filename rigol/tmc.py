# Copyright (c) 2021 by Phase Advanced Sensor Systems, Inc.
import usb.core

import btype


DEV_DEP_MSG_OUT            = 1
REQUEST_DEV_DEP_MSG_IN     = 2
DEV_DEP_MSG_IN             = 2
VENDOR_SPECIFIC_OUT        = 126
REQUEST_VENDOR_SPECIFIC_IN = 127
VENDOR_SPECIFIC_IN         = 127
TRIGGER                    = 128


STATUS_SUCCESS                  = 0x01
STATUS_PENDING                  = 0x02
STATUS_FAILED                   = 0x80
STATUS_TRANSFER_NOT_IN_PROGRESS = 0x81
STATUS_SPLIT_NOT_IN_PROGRESS    = 0x82
STATUS_SPLIT_IN_PROGRESS        = 0x83


class BulkOutHeader(btype.Struct):
    msgID          = btype.uint8_t()
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    data           = btype.Array(btype.uint8_t(), 8)
    _EXPECTED_SIZE = 12


class DevDepMsgOut(btype.Struct):
    msgID                = btype.uint8_t(DEV_DEP_MSG_OUT)
    bTag                 = btype.uint8_t()
    bTagInverse          = btype.uint8_t()
    rsrv1                = btype.uint8_t()
    transferSize         = btype.uint32_t()
    bmTransferAttributes = btype.uint8_t()
    rsrv2                = btype.Array(btype.uint8_t(), 3)
    _EXPECTED_SIZE       = 12


class RequestDevDepMsgIn(btype.Struct):
    msgID                = btype.uint8_t(REQUEST_DEV_DEP_MSG_IN)
    bTag                 = btype.uint8_t()
    bTagInverse          = btype.uint8_t()
    rsrv1                = btype.uint8_t()
    transferSize         = btype.uint32_t()
    bmTransferAttributes = btype.uint8_t()
    termChar             = btype.uint8_t()
    rsrv2                = btype.Array(btype.uint8_t(), 2)
    _EXPECTED_SIZE       = 12


class VendorSpecificOut(btype.Struct):
    msgID          = btype.uint8_t(VENDOR_SPECIFIC_OUT)
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    transferSize   = btype.uint32_t()
    rsrv2          = btype.Array(btype.uint8_t(), 4)
    _EXPECTED_SIZE = 12


class RequestVendorSpecificIn(btype.Struct):
    msgID          = btype.uint8_t(REQUEST_VENDOR_SPECIFIC_IN)
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    transferSize   = btype.uint32_t()
    rsrv2          = btype.Array(btype.uint8_t(), 4)
    _EXPECTED_SIZE = 12


class BulkInHeader(btype.Struct):
    msgID          = btype.uint8_t()
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    response       = btype.Array(btype.uint8_t(), 8)
    _EXPECTED_SIZE = 12


class DevDepMsgIn(btype.Struct):
    msgID                = btype.uint8_t(DEV_DEP_MSG_IN)
    bTag                 = btype.uint8_t()
    bTagInverse          = btype.uint8_t()
    rsrv1                = btype.uint8_t()
    transferSize         = btype.uint32_t()
    bmTransferAttributes = btype.uint8_t()
    rsrv2                = btype.Array(btype.uint8_t(), 3)
    _EXPECTED_SIZE       = 12


class VendorSpecificIn(btype.Struct):
    msgID          = btype.uint8_t(VENDOR_SPECIFIC_IN)
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    transferSize   = btype.uint32_t()
    rsrv2          = btype.Array(btype.uint8_t(), 4)
    _EXPECTED_SIZE = 12


class TriggerOut(btype.Struct):
    msgID          = btype.uint8_t(TRIGGER)
    bTag           = btype.uint8_t()
    bTagInverse    = btype.uint8_t()
    rsrv1          = btype.uint8_t()
    data           = btype.Array(btype.uint8_t(), 8)
    _EXPECTED_SIZE = 12


class GetCapabilities(btype.Struct):
    status                = btype.uint8_t()
    rsrv1                 = btype.uint8_t()
    bcdUCBTMC             = btype.uint16_t()
    interfaceCapabilities = btype.uint8_t()
    deviceCapabilities    = btype.uint8_t()
    rsrv2                 = btype.Array(btype.uint8_t(), 6)
    rsrv3                 = btype.Array(btype.uint8_t(), 12)


class TMCException(Exception):
    def __init__(self, msg, tmc_status):
        super().__init__(msg)
        self.tmc_status = tmc_status


class GetCapabilitiesException(TMCException):
    def __init__(self, msg, resp):
        super().__init__(msg, resp.status)
        self.resp = resp


class Device:
    def __init__(self, usb_dev):
        self.usb_dev         = usb_dev
        self.tag             = 0
        self.config          = None
        self.intf            = None
        self.bulk_in_ep      = None
        self.bulk_out_ep     = None
        self.interrupt_in_ep = None
        for config in self.usb_dev.configurations():
            for intf in config.interfaces():
                if intf.bInterfaceClass != 0xFE:
                    continue
                if intf.bInterfaceSubClass != 0x03:
                    continue
                if intf.bInterfaceProtocol != 0x01:
                    continue

                self.config = config
                self.intf   = intf
                for ep in intf.endpoints():
                    transfer_type = (ep.bmAttributes & 0x3)
                    if transfer_type == 2:
                        if ep.bEndpointAddress & 0x80:
                            assert self.bulk_in_ep is None
                            self.bulk_in_ep = ep
                        else:
                            assert self.bulk_out_ep is None
                            self.bulk_out_ep = ep
                    elif transfer_type == 3:
                        if ep.bEndpointAddress & 0x80:
                            assert self.interrupt_in_ep is None
                            self.interrupt_in_ep = ep

                assert self.bulk_in_ep is not None
                assert self.bulk_out_ep is not None

    def activate(self):
        try:
            self.usb_dev.get_active_configuration()
        except usb.core.USBError:
            self.usb_dev.set_configuration()

    def initiate_abort_bulk_out(self):
        raise NotImplementedError

    def check_abort_bulk_out_status(self):
        raise NotImplementedError

    def initiate_abort_bulk_in(self):
        raise NotImplementedError

    def check_abort_bulk_in_status(self):
        raise NotImplementedError

    def initiate_clear(self):
        raise NotImplementedError

    def check_clear_status(self):
        raise NotImplementedError

    def get_capabilities(self):
        data = self.usb_dev.ctrl_transfer(
            0xA1, 7, wIndex=self.intf.bInterfaceNumber, data_or_wLength=0x18)
        resp = GetCapabilities.unpack(data)
        if resp.status == STATUS_SUCCESS:
            return resp

        raise GetCapabilitiesException('GetCapabilities failed', resp)

    def indicator_pulse(self):
        raise NotImplementedError

    def new_tag(self):
        tag       = self.tag
        self.tag += 1
        return tag

    def send_dev_dep_msg(self, data):
        tag = self.new_tag()
        msg = DevDepMsgOut(
                bTag=tag,
                bTagInverse=(~tag & 0xFF),
                transferSize=len(data),
                bmTransferAttributes=0x01)
        pad = (-(msg._EXPECTED_SIZE + len(data)) % 4)
        cmd = msg.pack() + data + b'\x00'*pad
        assert len(cmd) <= self.bulk_out_ep.wMaxPacketSize
        self.bulk_out_ep.write(cmd)
        return tag

    def send_request_dev_dep_msg_in(self, transferSize=100):
        # Send a REQUEST_DEV_DEP_MSG_IN request to the device.
        tag = self.new_tag()
        msg = RequestDevDepMsgIn(
                bTag=tag,
                bTagInverse=(~tag & 0xFF),
                transferSize=transferSize)
        cmd = msg.pack()
        print(cmd)
        assert len(cmd) <= self.bulk_out_ep.wMaxPacketSize
        self.bulk_out_ep.write(cmd)
        return tag

    def recv_dev_dep_msg_in(self, transferSize=100):
        # Receive a DEV_DEP_MSG_IN response from the device.  The response is
        # terminated by a short packet.
        data = self.bulk_in_ep.read(DevDepMsgIn._EXPECTED_SIZE + transferSize)
        hdr  = DevDepMsgIn.unpack(data[:DevDepMsgIn._EXPECTED_SIZE])
        return hdr, data[DevDepMsgIn._EXPECTED_SIZE:]

    def query(self, cmd, transferSize=100):
        self.send_dev_dep_msg(cmd.encode())
        tag = self.send_request_dev_dep_msg_in(transferSize=transferSize)
        hdr, data = self.recv_dev_dep_msg_in(transferSize=transferSize)
        assert hdr.bTag == tag
        return hdr, bytes(data).decode()

    def query_bin(self, cmd_bytes, transferSize=100):
        self.send_dev_dep_msg(cmd_bytes)
        tag = self.send_request_dev_dep_msg_in(transferSize=transferSize)
        hdr, data = self.recv_dev_dep_msg_in(transferSize=transferSize)
        assert hdr.bTag == tag
        return hdr, bytes(data)
