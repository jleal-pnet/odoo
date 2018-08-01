# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner',
        string="GSTIN",
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('sale.order').partner_id,
        readonly=True, states={'draft': [('readonly', False)]}
        )
    l10n_in_reseller_partner_id = fields.Many2one('res.partner', 'Reseller', domain=[('vat', '!=', False)], states={'posted': [('readonly', True)]})
    l10n_in_place_of_supply = fields.Many2one(
        'res.country.state', string="Place Of Supply",readonly=True,
        states={'draft': [('readonly', False)]}, domain=[("country_id.code", "=", "IN")])

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['l10n_in_gstin_partner_id'] = self.l10n_in_gstin_partner_id.id
        invoice_vals['l10n_in_reseller_partner_id'] = self.l10n_in_reseller_partner_id.id
        invoice_vals['l10n_in_place_of_supply'] = self.l10n_in_place_of_supply.id
        return invoice_vals

    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id', 'l10n_in_gstin_partner_id')
    def onchange_partner_shipping_id(self):
        if self.partner_id.state_id.country_id.code == 'IN':
            self.l10n_in_place_of_supply = self.partner_id.state_id
        else:
            self.l10n_in_place_of_supply = self.env.ref('l10n_in.state_in_ot')
        return super(SaleOrder, self.with_context(l10n_in_gstin_partner_id=self.l10n_in_gstin_partner_id.id)).onchange_partner_shipping_id()
