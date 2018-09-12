# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartnerAutocompleteSync(models.Model):
    _name = 'res.partner.autocomplete.sync'

    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    sync_date = fields.Datetime('Sync datetime', default=False)
    error = fields.Char('Error', default=False)

    def _find_to_sync(self, partner_id=False):
        domain = [('sync_date', '=', False), ('error', '=', False)]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(domain)

    @api.model
    def start_sync(self):
        to_sync_items = self._find_to_sync()
        for to_sync_item in to_sync_items:
            partner = to_sync_item.partner_id

            params = {
                'company_data_id': partner.company_data_id,
            }

            if partner.vat and partner._is_vat_syncable(partner.vat):
                params['vat'] = partner.vat

            result, error = partner._rpc_remote_api('update', params)
            if result:
                to_sync_item.write({'sync_date': fields.Datetime.now()})
            else:
                to_sync_item.write({'error': error})

    def add_to_queue(self, partner_id):
        to_sync = self._find_to_sync(partner_id)
        if not to_sync:
            to_sync = self.create({'partner_id': partner_id})
        return to_sync
