# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class L10nInAccountInvoiceReport(models.Model):

    _inherit = "l10n_in.account.invoice.report"

    def _from(self):
        from_str = super(L10nInAccountInvoiceReport, self)._from()
        from_str += """AND aml.product_id::text != (
            CASE WHEN (SELECT key from ir_config_parameter where key = 'sale.default_deposit_product_id') 
            IS NULL Then '0'
            ELSE (SELECT key from ir_config_parameter where key = 'sale.default_deposit_product_id') END)"""
        return from_str
