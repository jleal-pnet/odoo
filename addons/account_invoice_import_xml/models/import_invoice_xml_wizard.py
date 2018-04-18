# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from lxml import etree

import base64


class ImportInvoiceXmlWizard(models.TransientModel):
    _name = 'account.invoice.xml.import'
    _description = 'Import Your Vendor Bills from XMLs Files.'

    attachment_ids = fields.Many2many('ir.attachment', 'xml_import_ir_attachments_rel',
        'xml_import_id', 'attachment_id', string='Attachments')

    @api.model
    def _get_xml_decoders(self):
        ''' List of usable decoders to extract invoice from attachments.

        :return: a list of triplet (xml_type, check_func, decode_func)
            * xml_type: The format name, e.g 'UBL 2.1'
            * check_func: A function taking an etree as parameter and returning a dict:
                * flag: The etree is part of this format.
                * error: Error message.
            * decode_func: A function taking an etree as parameter and returning an invoice record.
        '''
        # TO BE OVERWRITTEN
        return []

    @api.model
    def get_js_attachment_types(self, attachment_ids):
        ''' Retrieve the xml data for the widget JS-side.

        :param attachment_ids: A list of ids.
        :return: A dictionary mapping each attachment id with a dict:
            * type: the xml format (or None if unrecognized).
            * error: An error message.
        '''
        res = {}
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        decoders = self._get_xml_decoders()
        for attachment in attachments:
            vals = {
                'type': None,
                'error': _('File format not supported.'),
            }

            # Convert attachment -> etree
            content = base64.b64decode(attachment.datas)
            try:
                tree = etree.fromstring(content)
            except:
                res[attachment.id] = vals
                continue

            for xml_type, check_func, decode_func in decoders:
                check_res = check_func(tree)

                if check_res.get('flag'):
                    vals['type'] = xml_type
                    if check_res.get('error'):
                        vals['error'] = check_res['error']
                    else:
                        vals['error'] = None
                    break
            res[attachment.id] = vals
        return res

    @api.multi
    def create_invoices(self):
        ''' Create the invoices from attachments.

        :return: A action redirecting to account.invoice tree/form view.
        '''
        if not self.attachment_ids:
            return

        invoices = self.env['account.invoice']
        decoders = self._get_xml_decoders()
        for attachment in self.attachment_ids:

            # Convert attachment -> etree
            content = base64.b64decode(attachment.datas)
            try:
                tree = etree.fromstring(content)
            except:
                continue

            for xml_type, check_func, decode_func in decoders:
                check_res = check_func(tree)

                if check_res.get('flag') and not check_res.get('error'):
                    invoice = decode_func(tree)
                    if invoice:
                        invoices += invoice

                        attachment.write({
                            'res_model': 'account.invoice',
                            'res_id': invoice.id,
                        })

        action_vals = {
            'name': _('Invoices'),
            'domain': [('id', 'in', invoices.ids)],
            'view_type': 'form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        if len(invoices) == 1:
            action_vals.update({'res_id': invoices[0].id, 'view_mode': 'form'})
        else:
            action_vals['view_mode'] = 'tree,form'
        return action_vals
