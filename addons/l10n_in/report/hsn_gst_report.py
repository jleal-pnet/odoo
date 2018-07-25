# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class L10nInProductHsnReport(models.Model):

    _name = "l10n_in.product.hsn.report"
    _description = "Product HSN Statistics"
    _auto = False
    _order = 'date desc'

    account_move_id = fields.Many2one('account.move', string="Account Move")
    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one("product.product", string="Product")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    quantity = fields.Float(string="Product Qty")
    date = fields.Date(string="Date")
    price_total = fields.Float(string='Taxable Value')
    total = fields.Float(string="Total Value")
    igst_amount = fields.Float(string="Integrated Tax Amount")
    cgst_amount = fields.Float(string="Central Tax Amount")
    sgst_amount = fields.Float(string="State/UT Tax Amount")
    cess_amount = fields.Float(string="Cess Amount")
    company_id = fields.Many2one('res.company', string="Company")
    gstin_partner_id = fields.Many2one('res.partner', string="GSTIN")
    journal_id = fields.Many2one('account.journal', string="Journal")

    hsn_code = fields.Char(string="HSN")
    hsn_description = fields.Char(string="HSN description")

    l10n_in_uom_code = fields.Char(related='uom_id.l10n_in_code')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT aml.id AS id,
                aml.move_id AS account_move_id,
                aml.partner_id AS partner_id,
                aml.product_id,
                aml.product_uom_id AS uom_id,
                aml.quantity,
                aml.date_maturity AS date,
                ABS(aml.balance) As price_total,
                aml.l10n_in_igst_amount AS igst_amount,
                aml.l10n_in_cgst_amount AS cgst_amount,
                aml.l10n_in_sgst_amount AS sgst_amount,
                aml.l10n_in_cess_amount AS cess_amount,
                am.l10n_in_gstin_partner_id AS gstin_partner_id,
                am.journal_id,
                ABS(aml.balance) + aml.l10n_in_igst_amount + aml.l10n_in_cgst_amount + aml.l10n_in_sgst_amount + aml.l10n_in_cess_amount  AS total,
                aj.company_id,
                pt.l10n_in_hsn_code AS hsn_code,
                pt.l10n_in_hsn_description AS hsn_description
            FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN account_account aa ON aa.id = aml.account_id
                JOIN account_journal aj ON aj.id = am.journal_id
                JOIN product_product pp ON pp.id = aml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE aa.internal_type = 'other'
        )""" % (self._table))
