# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner',
        string="GSTIN Partner",
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('sale.order').partner_id,
        readonly=True, states={'draft': [('readonly', False)]}
        )

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['l10n_in_gstin_partner_id'] = self.l10n_in_gstin_partner_id.id
        return invoice_vals

    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id', 'l10n_in_gstin_partner_id')
    def onchange_partner_shipping_id(self):
        return super(SaleOrder, self.with_context(l10n_in_gstin_partner_id=self.l10n_in_gstin_partner_id.id)).onchange_partner_shipping_id()
