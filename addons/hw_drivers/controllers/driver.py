#!/usr/bin/python3
import logging
import time
from threading import Thread
import usb
import serial
import gatt
import evdev
import subprocess
from odoo import http
from urllib import request, parse
from uuid import getnode as get_mac

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
_logger = logging.getLogger('dispatcher')


class StatusController(http.Controller):

    @http.route('/drivers/status', type='http', auth='none', cors='*')
    def status(self):
        result = "<html><head></head><body>List of drivers and values: <br/> <ul>"
        for path in drivers:
            result += "<li>" + path + ":" + str(drivers[path].value) + "</li>"
        result += "</ul>"

        result +=" </body></html>"
        return result


    @http.route('/driverdetails/<string:identifier>', type='http', auth='none', cors='*')
    def statusdetail(self, identifier):
        for path in drivers:
            if identifier in path:
                return str(drivers[path].value)
            else:
                result = 'device not found'
        return result

#----------------------------------------------------------
# Driver common interface
#----------------------------------------------------------
class Driver(Thread):
#    def __init__(self, path):
#        pass

    def supported(self):
        pass

    def value(self):
        pass

    def run(self):
        pass

    def action(self, action):
        pass

#----------------------------------------------------------
# Usb drivers
#----------------------------------------------------------
usbdrivers = []
drivers = {}

class UsbMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(UsbMetaClass, cls).__new__(cls, clsname, bases, attrs)
        usbdrivers.append(newclass)
        return newclass


class USBDriver(Driver,metaclass=UsbMetaClass):
    def __init__(self, dev):
        super(USBDriver, self).__init__()
        self.dev = dev
        self.value = ""


class SylvacUSBDriver(USBDriver):

    def supported(self):
        return getattr(self.dev, 'idVendor') == 0x0403 and getattr(self.dev, 'idProduct') == 0x6001

    def value(self):
        return self.value

    def run(self):
        connection = serial.Serial('/dev/serial/by-id/usb-Sylvac_Power_USB_A32DV5VM-if00-port0',
                                   baudrate=4800,
                                   bytesize=7,
                                   stopbits=2,
                                   parity=serial.PARITY_EVEN)
        measure = b''
        no_except = True
        while no_except:
            try:
                char = connection.read(1)
                if ord(char) == 13:
                    # Let's send measure
                    self.value = measure.decode("utf-8")
                    measure = b''
                else:
                    measure += char
            except:
                no_except = False

    def action(self, action):
        pass

class KeyboardUSBDriver(USBDriver):

    def supported(self):
        return getattr(self.dev, 'idVendor') == 0x046d and getattr(self.dev, 'idProduct') == 0xc31c

    def value(self):
        return self.value
        
    def run(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if ('Keyboard' in device.name) & ('input0' in device.phys):
                path = device.path

        device = evdev.InputDevice(path)

        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                data = evdev.categorize(event)
                if data.scancode == 96:
                    return {}
                elif data.scancode == 28:
                    self.value = ''
                elif data.keystate:
                    self.value += data.keycode.replace('KEY_','')

    def action(self, action):
        pass


class BarcodeScannerdUSBDriver(USBDriver):

    def supported(self):
        return getattr(self.dev, 'idVendor') == 0x0c2e and getattr(self.dev, 'idProduct') == 0x0200

    def value(self):
        return self.value
        
    def run(self):

        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if ('Scanner' in device.name) & ('input0' in device.phys):
                path = device.path

        device = evdev.InputDevice(path)

        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                data = evdev.categorize(event)
                _logger.warning(data)
                if data.scancode == 96:
                    return {}
                elif data.scancode == 28:
                    _logger.warning(self.value)
                    self.value = ''
                elif data.keystate:
                    self.value += data.keycode.replace('KEY_','')

    def action(self, action):
        pass

class USBDeviceManager(Thread):
    devices = {}
    
    def run(self):
        while 1:
            devs = usb.core.find(find_all=True)
            updated_devices = {}
            for dev in devs:
                path =  "usb/%04x:%04x/%03d/%03d/" % (dev.idVendor, dev.idProduct, dev.bus, dev.address)
                updated_devices[path] = self.devices.get(path, dev)
            added = updated_devices.keys() - self.devices.keys()
            removed = self.devices.keys() - updated_devices.keys()
            self.devices = updated_devices
            if (removed):
                for path in list(drivers):
                    if (path in removed):
                        del drivers[path]
            for path in added:
                dev = updated_devices[path]
                for driverclass in usbdrivers:
                    _logger.info('For device %s checking driver %s', path, driverclass)
                    d = driverclass(updated_devices[path])
                    if d.supported():
                        _logger.info('For device %s will be driven', path)
                        lsusb = str(subprocess.check_output('lsusb')).split("\\n")
                        for usbtre in lsusb:
                            if "%04x:%04x" % (dev.idVendor, dev.idProduct) in usbtre:
                                name = usbtre.split("%04x:%04x" % (dev.idVendor, dev.idProduct))
                        send_device("%s" % (name[1]), "%04x:%04x" % (dev.idVendor, dev.idProduct))
                        drivers[path] = d
                        # launch thread
                        d.daemon = True
                        d.start()
            time.sleep(3)

subprocess.call("/home/pi/odoo/addons/point_of_sale/tools/posbox/configuration/inform_server.py")

def send_device(name, identifier):
    mac = get_mac()
    server = "" # read from file
    f = open('/home/pi/odoo-remote-server.conf', 'r')
    for line in f:
        server += line
    f.close()
    server = server.split('\n')[0]
    if server:
        url = server + "/iot2/"  # /check_device"
        values = {'iot_identifier': mac,
                  'name': name,
                  'identifier': identifier}
        data = parse.urlencode(values).encode()
        req = request.Request(url, data=data)
        try:
            response = request.urlopen(req)
        except:
            _logger.warning('Could not reach configured server')


udm = USBDeviceManager()
udm.daemon = True
udm.start()


#----------------------------------------------------------
# Bluetooth
#----------------------------------------------------------
class DeviceManager(gatt.DeviceManager):


    def device_discovered(self, device):
        # TODO: need some kind of updated_devices mechanism or not?
        for driverclass in btdrivers:
            d = driverclass(mac_address = device.mac_address, manager=self)
            path = "bt/%s/%s" % (device.mac_address, device.alias())
            if d.supported():
                if path not in drivers:
                    drivers[path] = d
                    d.connect()
                    print("New Driver", path, drivers)
                    #d.daemon=True
                    #d.run()
                #Otherwise, we should try to reanimate driver
                #else:
                #    print('Weird error with driver')
                #    drivers[path].run()
            #else:
            #    if path in drivers:
            #        print("Del driver", path)
            #        del drivers[path]
            #    del d
        #print("Discovered [%s] %s" % (device.mac_address, device.alias()))





#----------------------------------------------------------
# Bluetooth drivers
#----------------------------------------------------------

btdrivers = []

class BtMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(BtMetaClass, cls).__new__(cls, clsname, bases, attrs)
        btdrivers.append(newclass)
        return newclass


class BtDriver(metaclass=BtMetaClass):
    def __init__(self, mac_address, manager):
        pass #handled by gatt.Device

    def supported(self):
        pass

    def value(self):
        pass

    def run(self):
        pass

    def action(self, action):
        pass


class SylvacBluetoothDriver(BtDriver, gatt.Device):

    def supported(self):
        return self.device.alias() =="SY295"

    def value(self):
        return self.value

    def services_resolved(self):
        super().services_resolved()

        device_information_service = next(
            s for s in self.services
            if s.uuid == '00005000-0000-1000-8000-00805f9b34fb')

        measurement_characteristic = next(
            c for c in device_information_service.characteristics if c.uuid == '00005020-0000-1000-8000-00805f9b34fb')
        # m2 = next(c for c in device_information_service.characteristics if c.uuid == '00005021-0000-1000-8000-00805f9b34fb')
        # print m2.read_value()
        print('Check services')
        measurement_characteristic.enable_notifications()

    def characteristic_value_updated(self, characteristic, value):
        total = value[0] + value[1] * 256 + value[2] * 256 * 256 + value[3] * 256 * 256 * 256
        print('SY295', total / 1000000.0)

        # print "Supermeasurement ", characteristic, hex(value[0]), hex(value[1]), hex(value[2]), hex(value[3]), total

    def characteristic_enable_notification_succeeded(self):
        print("Success pied à coulisse Bluetooth!")

    def characteristic_enable_notification_failed(self):
        print("Problem connecting")

    def action(self, action):
        pass


#----------------------------------------------------------
# Agent ? Push values
#----------------------------------------------------------
# SDQFSQDFQSDF
#dm = DeviceManager(adapter_name='hci0')

#dm.start_discovery()
#dm.run()
#print("AFTER RUN")

#if __name__ == '__main__':
#print (usbdrivers)

#dm.start_discovery() #bluetooth
#dm.run() #bluetooth
#dm.main()



"""
# -*- coding: utf-8 -*-S
try:
    import usb.core
    import usb.util
except ImportError:
    usb = None
from threading import Thread
from urllib import request, parse
import os
import serial
import gatt

from uuid import getnode as get_mac
mac = get_mac()
server = "http://localhost:8069/"

url = server + "iot3/"#/check_box"
values = {'name': "IoT-on-laptop", 'identifier': mac}

data = parse.urlencode(values).encode()
req =  request.Request(url, data=data)
response = request.urlopen(req)

buses = {}


def send_device(name, identifier):
    url = server + "iot2/"  # /check_device"
    values = {'iot_identifier': mac,
              'name': name,
              'identifier': identifier}
    data = parse.urlencode(values).encode()
    req = request.Request(url, data=data)
    response = request.urlopen(req)

def send_message(device_identifier, message):
    url = server + "iot1/"  # /post_device"
    values = {'iot_identifier': mac,
              'device_identifier': device_identifier,
              'message': message}
    data = parse.urlencode(values).encode()
    req = request.Request(url, data=data)
    response = request.urlopen(req)

class HwProxy(object):
    def get_status(self):
        status = {}
        for bus in buses:
            status[bus] = buses[bus].get_status()
        return status


class UsbProxy(Thread):

    def run(self):
        # Check different
        # Check all drivers
        devices = usb.core.find(find_all=True)
        for dev in devices:
            # Basic conf, endpoints, ...
            for fact in usb_driver_factories:
                # Need a check to see if the device has no been registered already?

                # Continue...
                result = usb_driver_factories[fact].try_to_match_device(dev)
                if result:
                    send_device(result[0], result[1])

usb_driver_factories = {}
buses['usb'] = UsbProxy()


class AbstractUsbDriverFactory(object):  # No abstract class defined in current pos?

    def try_to_match_device(self, dev):
        pass

    def run(self):
        pass


active_usb_devices = {}


class MouseUsbDriverFactory(AbstractUsbDriverFactory):

    def try_to_match_device(self, dev):
        super(MouseUsbDriverFactory, self).try_to_match_device(dev)
        match = False
        if dev.idVendor == 1133 and dev.idProduct == 49271:
            match = True

        if match:  # code below might be put in constructor somehow
            if not active_usb_devices.get(dev.bcdDevice):
                if dev.is_kernel_driver_active(0):
                    dev.detach_kernel_driver(0)
                dev.set_configuration()
                cfg = dev.get_active_configuration()
                intf = cfg[(0, 0)]
                is_IN = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                ep = usb.util.find_descriptor(intf, custom_match=is_IN)
                active_usb_devices[dev.bcdDevice] = MouseUsbDriver(dev, ep)
                active_usb_devices[dev.bcdDevice].start()
                return ('Logitech USB Mouse', 'Mousy')  # No way to identify uniquely
        return False


usb_driver_factories['mouse'] = MouseUsbDriverFactory()


class MouseUsbDriver(Thread):

    def __init__(self, dev, in_point):
        super(MouseUsbDriver, self).__init__()
        self.in_point = in_point
        self.dev = dev

    def run(self):
        # Read something from the mouse
        while True:
            try:
                send_message('Mousy', self.dev.read(self.in_point.bEndpointAddress, self.in_point.wMaxPacketSize))
            except Exception as e:
                pass


class SerialProxy(Thread):
    def run(self):
        for fact in serial_driver_factories:
            result = serial_driver_factories[fact].try_to_match_device()
            if result:
                send_device(result[0], result[1])

serial_driver_factories = {}

buses['serial'] = SerialProxy()


class SylvacSerialDriverFactory():
    active_driver = False

    def try_to_match_device(self):
        try:
            files = os.listdir('/dev/serial/by-id')
        except:
            files = []
        if 'usb-Sylvac_Power_USB_A32DV5VM-if00-port0' in files:
            connection = serial.Serial('/dev/serial/by-id/usb-Sylvac_Power_USB_A32DV5VM-if00-port0',
                                       baudrate=4800,
                                       bytesize=7,
                                       stopbits=2,
                                       parity=serial.PARITY_EVEN)
            send_device('pied a coulisse', 'S_Calpro')
            self.active_driver = SylvacSerialDriver(connection)
            self.active_driver.start()
        #else:
        #    import pdb; pdb.set_trace()


serial_driver_factories['sylvac'] = SylvacSerialDriverFactory()

class SylvacSerialDriver(Thread):
    def __init__(self, connection):
        super(SylvacSerialDriver, self).__init__()
        self.connection = connection

    def run(self):
        measure = b''
        while True:
            char = self.connection.read(1)
            if ord(char) == 13:
                # Let's send measure
                send_message('S_Calpro', measure)
                measure = b''
            else:
                measure += char




HwProxy()
buses['usb'].start()
buses['serial'].start()
bluetooth_driver_factories = {}


class BluetoothProxy(gatt.DeviceManager):

    def device_discovered(self, device):
        for fact in bluetooth_driver_factories:
            bluetooth_driver_factories[fact].try_to_match_device(self, device.mac_address, device.alias())
        #print("Discovered [%s] %s" % (device.mac_address, device.alias()))


class SylvacBluetoothDriverFactory():
    active_driver = False

    def try_to_match_device(self, manager, mac, alias):
        if alias == 'SY295':
            if not self.active_driver:
                self.active_driver = mac
                send_device('SY295 pied à coulisse Bluetooth', mac)
                device = AnyDevice(mac_address=mac, manager=manager)
                device.connect()
                manager.run()

bluetooth_driver_factories['Sylvac'] = SylvacBluetoothDriverFactory()


class AnyDevice(gatt.Device):
    def services_resolved(self):
        super().services_resolved()

        device_information_service = next(
            s for s in self.services
            if s.uuid == '00005000-0000-1000-8000-00805f9b34fb')

        measurement_characteristic = next(
            c for c in device_information_service.characteristics if c.uuid == '00005020-0000-1000-8000-00805f9b34fb')
        # m2 = next(c for c in device_information_service.characteristics if c.uuid == '00005021-0000-1000-8000-00805f9b34fb')
        # print m2.read_value()
        measurement_characteristic.enable_notifications()

    def characteristic_value_updated(self, characteristic, value):
        total = value[0] + value[1] * 256 + value[2] * 256 * 256 + value[3] * 256 * 256 * 256
        send_message('SY295', total / 1000000.0)

        # print "Supermeasurement ", characteristic, hex(value[0]), hex(value[1]), hex(value[2]), hex(value[3]), total

    def characteristic_enable_notification_succeeded(self):
        print("Success pied à coulisse Bluetooth!")

    def characteristic_enable_notification_failed(self):
        print("Problem connecting")




try:
    manager = BluetoothProxy(adapter_name='hci0')
    buses['bluetooth'] = manager
    manager.start_discovery()
    manager.run()
    bluetooth_driver_factories['SY295'] = AnyDevice()
except:
    print("Please power on bluetooth")

"""
