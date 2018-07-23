# -*- coding:utf-8 -*-
#az Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class L10nInPaymentReport(models.AbstractModel):
    _name = "l10n_in.payment.report"

    account_move_id = fields.Many2one('account.move', string="Account Move")
    payment_id = fields.Many2one('account.payment', string='Payment')
    currency_id = fields.Many2one('res.currency', string="Currency")
    amount = fields.Float(string="Amount")
    payment_amount = fields.Float(string="Payment Amount")
    partner_id = fields.Many2one('res.partner', string="Customer")
    gstin_partner_id = fields.Many2one('res.partner', string="GSTIN Partner")
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
    journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one(related="journal_id.company_id", string="Company")
    partner_state_id = fields.Many2one('res.country.state', string="Partner State")
    place_of_supply = fields.Char(string="Place of Supply")
    supply_type = fields.Char(string="Supply Type")

    default_tax_id = fields.Many2one('account.tax', compute="_compute_default_tax_id", string="Default Tax")
    l10n_in_description = fields.Char(compute="_compute_l10n_in_description", string="Rate")
    igst_amount = fields.Float(compute="_compute_tax_amount", string="IGST amount")
    cgst_amount = fields.Float(compute="_compute_tax_amount", string="CGST amount")
    sgst_amount = fields.Float(compute="_compute_tax_amount", string="SGST amount")
    cess_amount = fields.Float(compute="_compute_tax_amount", string="CESS amount")

    #TO BE OVERWRITTEN
    @api.depends('currency_id')
    def _compute_tax_amount(self):
        """Calculate tax amount base on default tax set in company"""

    @api.depends('journal_id.company_id.account_sale_tax_id', 'journal_id.company_id.account_purchase_tax_id', 'supply_type')
    def _compute_default_tax_id(self):
        for record in self:
            default_sale_tax = record.journal_id.company_id.account_sale_tax_id
            default_purchase_tax = record.journal_id.company_id.account_purchase_tax_id
            record.default_tax_id = default_sale_tax if record.supply_type == 'outbound' else default_purchase_tax

    @api.depends('journal_id.company_id.account_sale_tax_id', 'journal_id.company_id.account_purchase_tax_id', 'supply_type')
    def _compute_l10n_in_description(self):
        for record in self:
            record.l10n_in_description = record.default_tax_id.l10n_in_description or '0'

    def _select(self):
        return """SELECT aml.id AS id,
            aml.move_id as account_move_id,
            ap.id AS payment_id,
            ap.l10n_in_gstin_partner_id AS gstin_partner_id,
            ap.payment_type,
            am.partner_id,
            am.amount AS payment_amount,
            ap.journal_id,
            aml.currency_id,
            p.state_id AS partner_state_id,
            (CASE WHEN ps.l10n_in_tin IS NOT NULL
                THEN concat(ps.l10n_in_tin,'-',ps.name)
                WHEN ps.l10n_in_tin IS NULL AND pc.code != 'IN'
                THEN '97-Other Territory'
                WHEN p.id IS NULL AND gstin_ps.l10n_in_tin IS NOT NULL
                THEN concat(gstin_ps.l10n_in_tin,'-',gstin_ps.name)
                ELSE ''
                END) AS place_of_supply,
            (CASE WHEN (ps.id = gstin_ps.id and ps.id IS NOT NULL and gstin_ps.id IS NOT NULL) or (p.id IS NULL)
                THEN 'Intra State'
                WHEN ps.id != gstin_ps.id and ps.id IS NOT NULL and gstin_ps.id IS NOT NULL or (ps.id IS NULL AND pc.code != 'IN')
                THEN 'Inter State'
                END) AS supply_type"""

    def _from(self):
        return """FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_payment ap ON ap.id = aml.payment_id
            JOIN account_account AS ac ON ac.id = aml.account_id
            LEFT JOIN res_partner p ON p.id = am.partner_id
            LEFT JOIN res_country pc ON pc.id = p.country_id
            LEFT JOIN res_country_state ps ON ps.id = p.state_id
            LEFT JOIN res_partner gstin_p ON gstin_p.id = ap.l10n_in_gstin_partner_id
            LEFT JOIN res_country_state gstin_ps ON gstin_ps.id = gstin_p.state_id
            """

    def _where(self):
        return """WHERE aml.payment_id IS NOT NULL
            AND ac.internal_type IN ('receivable', 'payable') AND am.state = 'posted'"""

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
            %s %s %s)""" % (self._table, self._select(), self._from(), self._where()))


class AdvancesPaymentReport(models.Model):

    _name = "l10n_in.advances.payment.report"
    _inherit = 'l10n_in.payment.report'
    _description = "Advances Payment Analysis"
    _auto = False

    date = fields.Date(string="Payment Date")
    reconcile_amount = fields.Float(string="Reconcile amount in Payment month")

    @api.depends('payment_amount', 'reconcile_amount', 'currency_id')
    def _compute_tax_amount(self):
        """Calculate tax amount base on default tax set in company"""
        account_move_line = self.env['account.move.line']
        for record in self:
            base_amount = record.payment_amount - record.reconcile_amount
            taxes_data = account_move_line._compute_l10n_in_tax(
                taxes=record.default_tax_id,
                price_unit=base_amount,
                currency=record.currency_id or None,
                quantity=1,
                partner=record.partner_id or None)
            record.igst_amount = taxes_data['igst_amount']
            record.cgst_amount = taxes_data['cgst_amount']
            record.sgst_amount = taxes_data['sgst_amount']
            record.cess_amount = taxes_data['cess_amount']

    def _select(self):
        select_str = super(AdvancesPaymentReport, self)._select()
        select_str += """,
            ap.payment_date as date,
            (SELECT sum(amount) FROM account_partial_reconcile AS apr
                WHERE (apr.credit_move_id = aml.id OR apr.debit_move_id = aml.id)
                AND (to_char(apr.max_date, 'MM-YYYY') = to_char(aml.date_maturity, 'MM-YYYY'))
            ) AS reconcile_amount,
            (am.amount - (SELECT (CASE WHEN SUM(amount) IS NULL THEN 0 ELSE SUM(amount) END) FROM account_partial_reconcile AS apr
                WHERE (apr.credit_move_id = aml.id OR apr.debit_move_id = aml.id)
                AND (to_char(apr.max_date, 'MM-YYYY') = to_char(aml.date_maturity, 'MM-YYYY'))
            )) AS amount"""
        return select_str


class L10nInAdvancesPaymentAdjustmentReport(models.Model):

    _name = "l10n_in.advances.payment.adjustment.report"
    _inherit = 'l10n_in.payment.report'
    _description = "Advances Payment Adjustment Analysis"
    _auto = False

    date = fields.Date('Reconcile Date')

    @api.depends('amount', 'currency_id', 'partner_id')
    def _compute_tax_amount(self):
        account_move_line = self.env['account.move.line']
        for record in self:
            taxes_data = account_move_line._compute_l10n_in_tax(
                taxes=record.default_tax_id,
                price_unit=record.amount,
                currency=record.currency_id or None,
                quantity=1,
                partner=record.partner_id or None)
            record.igst_amount = taxes_data['igst_amount']
            record.cgst_amount = taxes_data['cgst_amount']
            record.sgst_amount = taxes_data['sgst_amount']
            record.cess_amount = taxes_data['cess_amount']

    def _select(self):
        select_str = super(L10nInAdvancesPaymentAdjustmentReport, self)._select()
        select_str += """,
            apr.max_date AS date,
            apr.amount AS amount
            """
        return select_str

    def _from(self):
        from_str = super(L10nInAdvancesPaymentAdjustmentReport, self)._from()
        from_str += """
            JOIN account_partial_reconcile apr ON apr.credit_move_id = aml.id OR apr.debit_move_id = aml.id
            """
        return from_str

    def _where(self):
        where_str = super(L10nInAdvancesPaymentAdjustmentReport, self)._where()
        where_str += """
            AND (to_char(apr.max_date, 'MM-YYYY') > to_char(aml.date_maturity, 'MM-YYYY'))
        """
        return where_str
