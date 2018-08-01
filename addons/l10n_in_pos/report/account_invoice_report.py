# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class L10nInAccountInvoiceReport(models.Model):

    _inherit = "l10n_in.account.invoice.report"

    pos_order_id = fields.Many2one('pos.order', string="POS order")

    def _select(self):
        select_str = super(L10nInAccountInvoiceReport, self)._select()
        select_str = select_str.replace(
            "concat(am.id, '-', aml.l10n_in_tax_id, '-', aml.partner_id)",
            "concat(am.id, '-', aml.l10n_in_tax_id, '-', aml.partner_id, '-', aml.l10n_in_pos_order_id)")
        select_str = select_str.replace(
            "am.amount AS total,",
            """
            (CASE WHEN aml.l10n_in_pos_order_id IS NOT NULL
                THEN pos_order.amount_total
                ELSE am.amount
            END) AS total,
            """)
        select_str += """,
        aml.l10n_in_pos_order_id AS pos_order_id"""
        return select_str

    def _from(self):
        from_str = super(L10nInAccountInvoiceReport, self)._from()
        from_str = from_str.replace(
            """LEFT JOIN account_tax at ON at.id = aml.l10n_in_tax_id""",
            """LEFT JOIN account_tax at ON at.id = aml.l10n_in_tax_id
                LEFT JOIN pos_order pos_order ON pos_order.id = aml.l10n_in_pos_order_id"""
            )
        return from_str

    def _group_by(self):
        group_by_str = super(L10nInAccountInvoiceReport, self)._group_by()
        group_by_str += """,
            aml.l10n_in_pos_order_id,
            pos_order.amount_total
        """
        return group_by_str
