# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class IoTController(http.Controller):


    @http.route('/iot/check_trigger', type='json', auth='none')
    def check_trigger(self, device_id, key=None):
        workcenter_id = False
        # Call function to check in work
        result = self.env['iot.box'].check_trigger_devices(device_id, key)

    #get base url (might be used for authentication feature too)
    @http.route('/iot/base_url', type='json', auth='user')
    def get_base_url(self):
        config = request.env['ir.config_parameter'].search([('key', '=', 'web.base.url')], limit=1)
        if config:
            return config.value
        return 'Not Found'

    # Return home screen
    @http.route('/iot/box/<string:identifier>/screen_url', type='http', auth='public')
    def get_url(self, identifier):
        iotbox = request.env['iot.box'].sudo().search([('identifier', '=', identifier)], limit=1)
        if iotbox.screen_url:
            return iotbox.screen_url
        else:
            return 'http://localhost:8069/point_of_sale/display'

    @http.route('/iot/setup', type='json', auth='public')
    def update_box(self):
        data = request.jsonrequest

        # Update or create box
        box = request.env['iot.box'].sudo().search([('identifier', '=', data['identifier'])])
        if box:
            box = box[0]
            box.ip = data['ip']
            box.name = data['name']
        else:
            box = request.env['iot.box'].sudo().create({'name': data['name'], 'identifier': data['identifier'], 'ip': data['ip'], })

        trigger_dict = {}
        # Update or create devices
        for device_identifier in data['devices']:
            data_device = data['devices'][device_identifier]
            device = request.env['iot.device'].sudo().search([('iot_id', '=', box.id), ('identifier', '=', device_identifier)])
            if device:
                device.name = data_device['name']
            else:
                device = request.env['iot.device'].sudo().create({
                    'iot_id': box.id,
                    'name': data_device['name'],
                    'identifier': device_identifier,
                    'type': data_device['type'],
                    'connection': data_device['connection'],
                })
            # Return trigger-devices
            triggers = request.env['iot.trigger'].sudo().search([('device_id', '=', device.id)], limit=1)
            trigger_dict[device_identifier] = triggers and True or False
        return trigger_dict#json.dumps(trigger_dict).encode('utf8')

