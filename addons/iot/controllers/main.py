# -*- coding: utf-8 -*-
# import logging
#import os
#import re
#import time
#from collections import namedtuple
#from os import listdir
#from threading import Thread, Lock
from odoo import http
from odoo.http import request

class IoTController(http.Controller):

    @http.route('/get_url/<string:identifier>', type='http', auth='public')
    def get_url(self, identifier):
        iotbox = request.env['iot.box'].sudo().search([('identifier', '=', identifier)], limit=1)
        if iotbox:
            return iotbox.url
        else:
            return '' # Can not we throw 404?

    @http.route('/iotbox_conf', type='json', auth='public', csrf=False)
    def update_box(self):
        data = request.jsonrequest
        if 'iotbox' in data.keys():
            existing_box = request.env['iot.box'].sudo().search([('identifier', '=', data['iotbox']['identifier'])])
            if not existing_box:
                request.env['iot.box'].sudo().create({
                    'name': data['iotbox']['name'],
                    'identifier': data['iotbox']['identifier'],
                    'ip': data['iotbox']['ip'],
                })
            else:
                existing_box[0].ip = data['iotbox']['ip']
                existing_box[0].name = data['iotbox']['name']
            if 'devices' in data.keys():
                for device in data['devices'].keys():
                    existing_devices = request.env['iot.device'].sudo().search([('iot_id.identifier', '=', data['iotbox']['identifier']),('identifier', '=', device)])
                    if not existing_devices:
                        box = request.env['iot.box'].sudo().search([('identifier', '=', data['iotbox']['identifier'])], limit=1)
                        request.env['iot.device'].sudo().create({
                            'iot_id': box.id, #Might return error code when not successful
                            'name': data['devices'][device],
                            'identifier': device,
                        })

        return 'ok'
