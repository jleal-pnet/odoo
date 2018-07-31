# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner', string="GSTIN", required=True,
        default=lambda self: self.env['res.company']._company_default_get('stock.warehouse').partner_id
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('company_id') and not vals.get('l10n_in_gstin_partner_id'):
                vals['l10n_in_gstin_partner_id'] = self.env['res.company'].browse(vals.get('company_id')).partner_id.id
        return super(StockWarehouse, self).create(vals_list)
