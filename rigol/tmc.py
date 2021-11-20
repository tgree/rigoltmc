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
    _EXPECTED_SIZE = 24


class GetCapabilities488(btype.Struct):
    status                      = btype.uint8_t()
    rsrv1                       = btype.uint8_t()
    bcdUCBTMC                   = btype.uint16_t()
    usbtmcInterfaceCapabilities = btype.uint8_t()
    usbtmcDeviceCapabilities    = btype.uint8_t()
    rsrv2                       = btype.Array(btype.uint8_t(), 6)
    bcdUSB488                   = btype.uint16_t()
    usb488InterfaceCapabilities = btype.uint8_t()
    usb488DeviceCapabilities    = btype.uint8_t()
    rsrv3                       = btype.Array(btype.uint8_t(), 8)
    _EXPECTED_SIZE = 24


class TMCException(Exception):
    def __init__(self, msg, tmc_status):
        super().__init__(msg)
        self.tmc_status = tmc_status


class GetCapabilitiesException(TMCException):
    def __init__(self, msg, resp):
        super().__init__(msg, resp.status)
        self.resp = resp


class Device:
    def __init__(self, usb_dev, allowed_protocols=(0x00,)):
        self.usb_dev         = usb_dev
        self.tag             = 2
        self.config          = None
        self.intf            = None
        self.bulk_in_ep      = None
        self.bulk_out_ep     = None
        self.interrupt_in_ep = None
        for config in self.usb_dev.configurations():
            for intf in config.interfaces():
                if intf.bInterfaceClass != 0xFE:        # Application-Class
                    continue
                if intf.bInterfaceSubClass != 0x03:     # USBTMC
                    continue
                if intf.bInterfaceProtocol not in allowed_protocols:
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

        self.max_out_size = self.bulk_out_ep.wMaxPacketSize

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
        tag = self.tag
        self.tag += 1
        if self.tag == 128:
            self.tag = 2
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
        assert len(cmd) <= self.max_out_size
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
        assert len(cmd) <= self.max_out_size
        self.bulk_out_ep.write(cmd)
        return tag

    def recv_dev_dep_msg_in(self):
        raise NotImplementedError

    def cmd(self, cmd):
        self.send_dev_dep_msg(cmd.encode())

    def query(self, cmd, transferSize=100):
        self.send_dev_dep_msg(cmd.encode())
        tag = self.send_request_dev_dep_msg_in(transferSize=transferSize)
        hdr, data = self.recv_dev_dep_msg_in()
        assert hdr.bTag == tag
        return hdr, bytes(data).decode()

    def exec(self, cmd, **kwargs):
        if cmd.strip()[-1] == '?':
            return self.query(cmd, **kwargs)
        return self.cmd(cmd, **kwargs)

    def cmd_bin(self, cmd):
        self.send_dev_dep_msg(cmd)

    def query_bin(self, cmd_bytes, transferSize=100):
        self.send_dev_dep_msg(cmd_bytes)
        tag = self.send_request_dev_dep_msg_in(transferSize=transferSize)
        hdr, data = self.recv_dev_dep_msg_in()
        assert hdr.bTag == tag
        return hdr, bytes(data)

    def exec_bin(self, cmd, **kwargs):
        if cmd.strip()[-1:] == b'?':
            return self.query_bin(cmd, **kwargs)
        return self.cmd_bin(cmd, **kwargs)


class USB488Device(Device):
    def __init__(self, usb_dev):
        super().__init__(usb_dev, allowed_protocols=(0x01,))

    def get_capabilities(self):
        data = self.usb_dev.ctrl_transfer(
            0xA1, 7, wIndex=self.intf.bInterfaceNumber, data_or_wLength=0x18)
        resp = GetCapabilities488.unpack(data)

        if resp.status == STATUS_SUCCESS:
            return resp

        raise GetCapabilitiesException('GetCapabilities488 failed', resp)

    def read_status_byte(self):
        tag  = self.new_tag()
        data = self.usb_dev.ctrl_transfer(
            0xA1, 128, wIndex=self.intf.bInterfaceNumber, data_or_wLength=3,
            wValue=tag)
        if data[0] != STATUS_SUCCESS:
            raise Exception('Read status byte failed: %u' % data[0])
        assert data[1] == tag

        if self.interrupt_in_ep is not None:
            assert data[2] == 0x00
            data = self.interrupt_in_ep.read(2)
            assert data[0] == (0x80 | tag)
            return data[1]

        return data[2]

    def ren_control(self):
        raise NotImplementedError

    def go_to_local(self):
        raise NotImplementedError

    def local_lockout(self):
        raise NotImplementedError
