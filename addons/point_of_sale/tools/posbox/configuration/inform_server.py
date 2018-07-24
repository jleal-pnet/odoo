#!/usr/bin/python3

# Part that sends stuff to the internet
from urllib import request, parse
from uuid import getnode as get_mac
import subprocess
import netifaces as ni
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
_logger = logging.getLogger('dispatcher')

macline = subprocess.check_output("/sbin/ifconfig eth0 |grep 'ether '", shell=True).decode('utf-8')
mac = macline.split(' ')
server = "" # read from file
url = ""
try:
    f = open('/home/pi/odoo-remote-server.conf', 'r')
    for line in f:
        server += line
    f.close()
except:
    pass

if server:
    server = server.split('\n')[0]
    url = server + "/iot3/"#/check_box"
    interfaces = ni.interfaces()
    for iface_id in interfaces:
        iface_obj = ni.ifaddresses(iface_id)
        ifconfigs = iface_obj.get(ni.AF_INET, [])
        for conf in ifconfigs:
            if conf.get('addr') and conf.get('addr') != '127.0.0.1':
                ips = conf.get('addr')
                break

    hostname = subprocess.check_output('hostname')
    values = {'name': hostname,
                'identifier': mac[9],
                'ip': ips}
    data = parse.urlencode(values).encode()
    req =  request.Request(url, data=data)
    try:
        response = request.urlopen(req)
    except:
        _logger.warning('Could not reach configured server')