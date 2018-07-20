# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner',
        string="GSTIN Partner",
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('purchase.order').partner_id,
        readonly=True, states={'draft': [('readonly', False)]}
        )
