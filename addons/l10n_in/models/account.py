# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #For use in GSTR report.
    l10n_in_igst_amount = fields.Float(string="IGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_cgst_amount = fields.Float(string="CGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_sgst_amount = fields.Float(string="SGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_cess_amount = fields.Float(string="CESS Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_tax_price_unit = fields.Float(string="Tax Base Amount")

    @api.depends('l10n_in_tax_price_unit', 'tax_ids', 'quantity', 'product_id', 'partner_id', 'company_currency_id')
    def _compute_l10n_in_taxes_amount(self):
        for line in self:
            taxes_data = line._compute_l10n_in_tax(
                taxes=line.tax_ids,
                price_unit=line.l10n_in_tax_price_unit,
                currency=line.company_currency_id or None,
                quantity=line.quantity,
                product=line.product_id or None,
                partner=line.partner_id or None)
            line.l10n_in_igst_amount = taxes_data['igst_amount']
            line.l10n_in_cgst_amount = taxes_data['cgst_amount']
            line.l10n_in_sgst_amount = taxes_data['sgst_amount']
            line.l10n_in_cess_amount = taxes_data['cess_amount']

    def _compute_l10n_in_tax(self, taxes, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """common method to compute gst tax amount base on tax group"""
        res = {'igst_amount': 0.0, 'sgst_amount': 0.0, 'cgst_amount': 0.0, 'cess_amount': 0.0}
        AccountTax = self.env['account.tax']
        igst_group = self.env.ref('l10n_in.igst_group', False)
        cgst_group = self.env.ref('l10n_in.cgst_group', False)
        sgst_group = self.env.ref('l10n_in.sgst_group', False)
        cess_group = self.env.ref('l10n_in.cess_group', False)
        filter_tax = taxes.filtered(lambda t: t.type_tax_use != 'none')
        for tax_data in filter_tax.compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)['taxes']:
            tax = AccountTax.browse(tax_data['id'])
            tax_group_id = tax.tax_group_id.id
            if tax_group_id == (sgst_group and sgst_group.id or False):
                res['sgst_amount'] += tax_data['amount']
            if tax_group_id == (cgst_group and cgst_group.id or False):
                res['cgst_amount'] += tax_data['amount']
            if tax_group_id == (igst_group and igst_group.id or False):
                res['igst_amount'] += tax_data['amount']
            if tax_group_id == (cess_group and cess_group.id or False):
                res['cess_amount'] += tax_data['amount']
        return res
