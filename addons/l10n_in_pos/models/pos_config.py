# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner',
        string="GSTIN Partner",
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('pos.config').partner_id,
        domain="[('l10n_in_company_id', '=', company_id)]"
        )

    @api.onchange('stock_location_id', 'company_id')
    def _onchange_l10n_in_pos_gstin_partner(self):
        warehouse_partner = self.stock_location_id.get_warehouse().partner_id
        self.l10n_in_gstin_partner_id = warehouse_partner and warehouse_partner.id or self.company_id.partner_id.id
