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

    @api.onchange('partner_id', 'company_id', 'l10n_in_gstin_partner_id')
    def onchange_partner_id(self):
        return super(PurchaseOrder, self.with_context(l10n_in_gstin_partner_id=self.l10n_in_gstin_partner_id.id)).onchange_partner_id()
