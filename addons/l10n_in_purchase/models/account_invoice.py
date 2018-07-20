# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self.purchase_id:
            self.l10n_in_gstin_partner_id = self.purchase_id.l10n_in_gstin_partner_id.id
        return super(AccountInvoice, self).purchase_order_change()

    @api.onchange('company_id')
    def _onchange_l10n_in_company(self):
        if not self.env.context.get('from_purchase_order_change'):
            self.l10n_in_gstin_partner_id = self.company_id.partner_id