#!/usr/bin/python3
import logging
import time
from threading import Thread
import usb
import serial
import gatt
import evdev
import subprocess
import netifaces as ni
import json
import re
from odoo import http
import urllib3
from odoo.http import request as httprequest

from uuid import getnode as get_mac

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
_logger = logging.getLogger('dispatcher')

to_reload = {}
last_ping = {}

class StatusController(http.Controller):


    @http.route('/box/check_reload', type='http', auth='none', cors='*')
    def connect_box(self, tab_id, workcenter_id):
        if not tab_id:
            #check new id
            tab_id = max(to_reload.keys() + 1)
            return tab_id
        if tab_id and workcenter_id:
            if to_reload.get[tab_id]:
                if to_reload[tab_id].get(workcenter_id):
                    if to_reload[tab_id][workcenter_id]:
                        result = to_reload[tab_id][workcenter_id]
                        to_reload[tab_id][workcenter_id] = ''
                    else:
                        to_reload[tab_id][workcenter_id] = ''


    def click_pedal(self, path):
        # use urllib3
        # Call server with pedal
        # server.check_pedal(device_id)
        pass

    owner_dict = {}

    @http.route('/owner/check', type='json', auth='none', cors='*', csrf=False)
    def check_cantakeowner(self): #, devices, tab
        data = httprequest.jsonrequest
        for device in data['devices']:
            if self.owner_dict.get(device) and self.owner_dict[device] != data['tab']:
                return 'no'
        return 'yes'

    @http.route('/owner/take', type='json', auth='none', cors='*', csrf=False)
    def take_ownership(self): #, devices, tab
        data = httprequest.jsonrequest
        for device in data['devices']:
            self.owner_dict[device] = data['tab']
        return data['tab']

    @http.route('/owner/ping', type='json', auth='none', cors='*', csrf=False)
    def ping_trigger(self): #, tab
        data = httprequest.jsonrequest
        ping_dict = {}
        #last_ping[data['tab']] = datetime.datetime.utcnow()
        for dev in data['devices']:
            if self.owner_dict.get(dev) and self.owner_dict[dev] == data['tab']:
                if drivers[dev].ping_value:
                    ping_dict[dev] = drivers[dev].ping_value
                    drivers[dev].ping_value = '' #or set it to nothing
            else:
                ping_dict[dev] = 'STOP'
        return ping_dict

    @http.route('/box/connect', type='http', auth='none', cors='*', csrf=False)
    def connect_box(self, url):
        server = ""  # read from file
        try:
            f = open('/home/pi/odoo-remote-server.conf', 'r')
            for line in f:
                server += line
            f.close()
            server = server.split('\n')[0]
        except:
            server = ''
        if server:
            return 'This IoTBox had already been connected'
        else:
            subprocess.call("/home/pi/odoo/addons/point_of_sale/tools/posbox/configuration/connect_to_server.sh " + url, shell=True)
            return 'IoTBox connected'

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
        if drivers.get(identifier):
            return str(drivers[identifier].value)
        return 'device not found'

    @http.route('/driveraction/<string:identifier>', type='json', auth='none', cors='*', csrf=False)
    def driveraction(self, identifier):
        data = httprequest.jsonrequest
        result = 'device not found'
        if data.get('action') == 'print':
            with open('/tmp/toprinter', 'w') as file:
                file.write(data['data'])
            subprocess.call("cat /tmp/toprinter | base64 -d | lp -d " + identifier, shell=True)
            result = 'ok'
        if data.get('action') == 'camera':
            cameras = subprocess.check_output("v4l2-ctl --list-devices", shell=True).decode('utf-8').split('\n\n')
            adrress = '/dev/video0'
            for camera in cameras:
                if camera:
                    camera = camera.split('\n\t')
                    serial = re.sub('[^a-zA-Z0-9 ]+', '', camera[0].split(': ')[0]).replace(' ','_')
                    if serial == data.get('identifier'):
                        adrress = camera[1]
            picture = subprocess.check_output("v4l2-ctl --list-formats-ext|grep 'Size'|awk NR==1'{print $3}'", shell=True).decode('utf-8')
            subprocess.call("fswebcam -d " + adrress + " /tmp/testimage -r " + picture, shell=True)
            image_bytes = subprocess.check_output('cat /tmp/testimage | base64',shell=True)
            result = {'image': image_bytes}
        return result

    @http.route('/send_iot_box', type='http', auth='none', cors='*')
    def send_iot_box(self):
        send_iot_box_device()
        return 'ok'


#----------------------------------------------------------
# Driver common interface
#----------------------------------------------------------
class Driver(Thread):

    trigger = False
    def setTrigger(self, trigger):
        self.trigger = trigger

    def supported(self):
        pass

    def value(self):
        pass

    def get_name(self):
        pass

    def get_connection(self):
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

    def get_name(self):
        lsusb = str(subprocess.check_output('lsusb')).split("\\n")
        for usbpath in lsusb:  # Should filter on usb devices or inverse loops?
            device = self.dev
            if "%04x:%04x" % (device.idVendor, device.idProduct) in usbpath:
                return usbpath.split("%04x:%04x" % (device.idVendor, device.idProduct))[1]
        return str(device.idVendor) + ":" + str(device.idProduct)

    def get_connection(self):
        return 'direct'

    def value(self):
        return self.value


class SylvacUSBDriver(USBDriver):

    def supported(self):
        return getattr(self.dev, 'idVendor') == 0x0403 and getattr(self.dev, 'idProduct') == 0x6001

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

    ping_value = ''
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
                    self.ping_value = data.keycode.replace('KEY_','')


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
        first_time = True
        while 1:
            sendJSON = False
            devs = usb.core.find(find_all=True)
            updated_devices = {}
            for dev in devs:
                path =  "usb_%04x:%04x_%03d_%03d_" % (dev.idVendor, dev.idProduct, dev.bus, dev.address)
                updated_devices[path] = self.devices.get(path, dev)
            added = updated_devices.keys() - self.devices.keys()
            removed = self.devices.keys() - updated_devices.keys()
            self.devices = updated_devices
            if (removed):
                for path in list(drivers):
                    if (path in removed):
                        del drivers[path]
                        sendJSON = True
            for path in added:
                dev = updated_devices[path]
                for driverclass in usbdrivers:
                    _logger.info('For device %s checking driver %s', path, driverclass)
                    d = driverclass(updated_devices[path])
                    if d.supported():
                        _logger.info('For device %s will be driven', path)
                        drivers[path] = d
                        # launch thread
                        d.daemon = True
                        d.start()
                        sendJSON = True
            if sendJSON or first_time:
                send_iot_box_device(send_printer = first_time)
                first_time = False
            time.sleep(3)
            




def send_iot_box_device(send_printer):
    maciotbox = subprocess.check_output("/sbin/ifconfig eth0 |grep -Eo ..\(\:..\){5}", shell=True).decode('utf-8').split('\n')[0]
    server = "" # read from file
    try:
        f = open('/home/pi/odoo-remote-server.conf', 'r')
        for line in f:
            server += line
        f.close()
    except: #In case the file does not exist
        server=''
    server = server.split('\n')[0]
    if server:
        url = server + "/iot/setup"
        interfaces = ni.interfaces()
        for iface_id in interfaces:
            iface_obj = ni.ifaddresses(iface_id)
            ifconfigs = iface_obj.get(ni.AF_INET, [])
            for conf in ifconfigs:
                if conf.get('addr') and conf.get('addr') != '127.0.0.1':
                    ips = conf.get('addr')
                    break

        # Build device JSON
        devicesList = {}
        for path in drivers:
            device_name = drivers[path].get_name()
            device_connection = drivers[path].get_connection()
            devicesList[path] = {'name': device_name,
                                 'type': 'device',
                                 'connection': device_connection}



        # Build camera JSON
        try:
            cameras = subprocess.check_output("v4l2-ctl --list-devices", shell=True).decode('utf-8').split('\n\n')
            for camera in cameras:
                if camera:
                    camera = camera.split('\n\t')
                    serial = re.sub('[^a-zA-Z0-9 ]+', '', camera[0].split(': ')[0]).replace(' ','_')
                    devicesList[serial] = {
                                            'name': camera[0].split(': ')[0],
                                            'connection': 'direct',
                                            'type': 'camera'
                                        }
        except:
            pass

        # Build printer JSON
        printerList = {}
        if send_printer:
            printers = subprocess.check_output("sudo lpinfo -lv", shell=True).decode('utf-8').split('Device')
            for printer in printers:
                printerTab = printer.split('\n')
                if printer and printerTab[4].split('=')[1] != ' ':
                    device_connection = printerTab[1].split('= ')[1]
                    model = ''
                    for device_id in printerTab[4].split('= ')[1].split(';'):
                        if any(x in device_id for x in ['MDL','MODEL']):
                            model = device_id.split(':')[1]
                    name = printerTab[2].split('= ')[1]
                    serial = re.sub('[^a-zA-Z0-9 ]+', '', model).replace(' ','_')
                    identifier = ''
                    if device_connection == 'direct':
                        identifier = serial + '_' + maciotbox  #name + macIOTBOX
                    elif device_connection == 'network' and 'socket' in printerTab[0]:
                        socketIP = printerTab[0].split('://')[1]
                        macprinter = subprocess.check_output("arp -a " + socketIP + " |awk NR==1'{print $4}'", shell=True).decode('utf-8').split('\n')[0]
                        identifier = macprinter  # macPRINTER
                    elif device_connection == 'network' and 'dnssd' in printerTab[0]:
                        hostname_printer = subprocess.check_output("ippfind -n \"" + model + "\" | awk \'{split($0,a,\"/\"); print a[3]}\' | awk \'{split($0,b,\":\"); print b[1]}\'", shell=True).decode('utf-8').split('\n')[0]
                        if hostname_printer:
                            macprinter = subprocess.check_output("arp -a " + hostname_printer + " |awk NR==1'{print $4}'", shell=True).decode('utf-8').split('\n')[0]
                            identifier = macprinter  # macprinter

                    identifier = identifier.replace(':','_')
                    if identifier and identifier not in printerList:
                        printerList[identifier] = {
                                            'name': model,
                                            'connection': device_connection,
                                            'type': 'printer'
                        }
                        # install these printers
                        try:
                            ppd = subprocess.check_output("sudo lpinfo -m |grep '" + model + "'", shell=True).decode('utf-8').split('\n')
                            if len(ppd) > 2:
                                subprocess.call("sudo lpadmin -p '" + identifier + "' -E -v '" + printerTab[0].split('= ')[1] + "'", shell=True)
                            else:
                                subprocess.call("sudo lpadmin -p '" + identifier + "' -E -v '" + printerTab[0].split('= ')[1] + "' -m '" + ppd[0].split(' ')[0] + "'", shell=True)
                        except:
                            subprocess.call("sudo lpadmin -p '" + identifier + "' -E -v '" + printerTab[0].split('= ')[1] + "'", shell=True)

        #build JSON with all devices
        hostname = subprocess.check_output('hostname').decode('utf-8').split('\n')[0]
        data = {'name': hostname,'identifier': maciotbox, 'ip': ips}
        devicesList.update(printerList)
        data['devices'] = devicesList
        data_json = json.dumps(data).encode('utf8')
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        http = urllib3.PoolManager()
        req = False
        try:
            req = http.request('POST',
                                url,
                                body=data_json,
                                headers=headers)
        except:
            _logger.warning('Could not reach configured server')
#        if req:
#            # recuperate json dict
#            # Could check status 200 also
#            data_json = json.loads(req.data.decode('utf-8'))
#            device_dict = data_json['result']
#            for dev in device_dict:
#                drivers[dev].setTrigger(device_dict[dev])


def check_trigger(device, key):
    server = ""  # read from file
    try:
        f = open('/home/pi/odoo-remote-server.conf', 'r')
        for line in f:
            server += line
        f.close()
    except:  # In case the file does not exist
        server = ''
    server = server.split('\n')[0]
    if server:
        url = server + "/iot/check_trigger"
        data = {'device_id': device, 'key': key}
        data_json = json.dumps(data).encode('utf8')
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        http = urllib3.PoolManager()
        try:
            req = http.request('POST',
                                url,
                                body=data_json,
                                headers=headers)
        except:
            _logger.warning('Could not reach configured server')





udm = USBDeviceManager()
udm.daemon = True
udm.start()


#----------------------------------------------------------
# Bluetooth
#----------------------------------------------------------
class GattBtManager(gatt.DeviceManager):

    def device_discovered(self, device):
        # TODO: need some kind of updated_devices mechanism or not?
        for driverclass in btdrivers:
            d = driverclass(device = device)
            path = "bt_%s" % (device.mac_address,)
            if d.supported():
                if path not in drivers:
                    drivers[path] = d
                    d.connect()
                    send_iot_box_device(False)
                    print("New Driver", path, drivers)


class BtManager(Thread):
    gatt_manager = False

    def run(self):
        dm = GattBtManager(adapter_name='hci0')
        self.gatt_manager = dm
        dm.start_discovery()
        dm.run()




#----------------------------------------------------------
# Bluetooth drivers
#----------------------------------------------------------

btdrivers = []

class BtMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(BtMetaClass, cls).__new__(cls, clsname, bases, attrs)
        btdrivers.append(newclass)
        return newclass


class BtDriver(Driver, metaclass=BtMetaClass):


    def __init__(self, device):
        super(BtDriver, self).__init__()
        self.dev = device
        self.value = ''
        self.gatt_device = False

    def get_name(self):
        return self.dev.alias()

    def value(self):
        return self.value

    def action(self, action):
        pass

    def get_connection(self):
        return 'bluetooth'

    def connect(self):
        pass


class SylvacBtDriver(BtDriver):

    def supported(self):
        return self.dev.alias() == "SY295" or self.dev.alias() == "SY276"

    def connect(self):
        self.gatt_device = GattSylvacBtDriver(mac_address=self.dev.mac_address, manager=bm.gatt_manager)
        self.gatt_device.btdriver = self
        self.gatt_device.connect()


class GattSylvacBtDriver(gatt.Device):
    btdriver = False

    def services_resolved(self):
        super().services_resolved()

        device_information_service = next(
            s for s in self.services
            if s.uuid == '00005000-0000-1000-8000-00805f9b34fb')

        measurement_characteristic = next(
            c for c in device_information_service.characteristics if c.uuid == '00005020-0000-1000-8000-00805f9b34fb')
        measurement_characteristic.enable_notifications()

    def characteristic_value_updated(self, characteristic, value):
        total = value[0] + value[1] * 256 + value[2] * 256 * 256 + value[3] * 256 * 256 * 256
        if total > 256 ** 4 / 2:
            total = total - 256 ** 4
        self.btdriver.value = total / 1000000.0

    def characteristic_enable_notification_succeeded(self):
        print("Success pied à coulisse Bluetooth!")

    def characteristic_enable_notification_failed(self):
        print("Problem connecting")


#----------------------------------------------------------
#Bluetooth start
#----------------------------------------------------------
bm = BtManager()
bm.daemon = True
bm.start()
