# -*- coding: utf-8 -*-
#import logging
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
        iotbox = request.env['iot.box'].sudo().search([], limit=1) #('identifier', '=', identifier)
        if iotbox:
            return iotbox.url
        else:
            return '' # Can not we throw 404?

    @http.route('/iot2', type='http', auth='public', csrf=False)
    def update_device(self, iot_identifier, name, identifier):
        # Search id of iotbox that corresponds to this identifier
        existing_devices = request.env['iot.device'].sudo().search([('iot_id.identifier', '=', iot_identifier),
                                                               ('identifier', '=', identifier)])
        if not existing_devices:
            box = request.env['iot.box'].sudo().search([('identifier', '=', iot_identifier)], limit=1)
            request.env['iot.device'].sudo().create({
                'iot_id': box.id, #Might return error code when not successful
                'name': name,
                'identifier': identifier,
            })
        return 'ok'

    @http.route('/iot3', type='http', auth='public', csrf=False)
    def update_box(self, name, identifier, ip):
        existing_box = request.env['iot.box'].sudo().search([('identifier', '=', identifier)])
        if not existing_box:
            request.env['iot.box'].sudo().create({
                'name': name,
                'identifier': identifier,
                'ip': ip,
            })
        else:
            existing_box[0].ip = ip #Might set name to

        return 'ok'
