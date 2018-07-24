# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class L10nInExemptedReport(models.Model):

    _name = "l10n_in.exempted.report"
    _description = "Exempted Gst Supplied Statistics"
    _auto = False

    account_move_id = fields.Many2one('account.move', string="Account Move")
    out_supply_type = fields.Char(string="Outward Supply Type")
    in_supply_type = fields.Char(string="Inward Supply Type")
    nil_rated_amount = fields.Float("Nil rated supplies")
    exempted_amount = fields.Float("Exempted")
    non_gst_supplies = fields.Float("Non GST Supplies")
    date = fields.Date("Date")
    company_id = fields.Many2one('res.company', string="Company")
    gstin_partner_id = fields.Many2one('res.partner', string="GSTIN")
    journal_id = fields.Many2one('account.journal', string="Journal")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT aml.id AS id,
                    aml.date_maturity AS date,
                    ABS(aml.balance) AS price_total,
                    am.l10n_in_gstin_partner_id AS gstin_partner_id,
                    am.journal_id,
                    aj.company_id,
                    aml.move_id as account_move_id,

                    (CASE WHEN (p.state_id = gstin_p.state_id and p.id IS NOT NULL and gstin_p.state_id IS NOT NULL) or (p.id IS NULL)
                        THEN (CASE WHEN p.vat IS NOT NULL
                            THEN 'Intra-State supplies to registered persons'
                            ELSE 'Intra-State supplies to unregistered persons'
                            END)
                        WHEN p.state_id != gstin_p.state_id and p.state_id IS NOT NULL and gstin_p.state_id IS NOT NULL or (p.state_id IS NULL AND pc.code != 'IN')
                        THEN (CASE WHEN p.vat IS NOT NULL
                            THEN 'Inter-State supplies to registered persons'
                            ELSE 'Inter-State supplies to unregistered persons'
                            END)
                    END) AS out_supply_type,

                    (CASE WHEN (p.state_id = gstin_p.state_id and p.id IS NOT NULL and gstin_p.state_id IS NOT NULL) or (p.id IS NULL)
                    THEN 'Intra-State supplies'
                    WHEN p.state_id != gstin_p.state_id and p.state_id IS NOT NULL and gstin_p.state_id IS NOT NULL or (p.state_id IS NULL AND pc.code != 'IN')
                    THEN 'Inter-State supplies'
                    END) AS in_supply_type,

                    (CASE WHEN (
                        SELECT MAX(account_tax_id) FROM account_move_line_account_tax_rel
                            JOIN account_tax at ON at.id = account_tax_id
                            WHERE account_move_line_id = aml.id AND at.tax_group_id IN
                             ((SELECT res_id FROM ir_model_data WHERE module='l10n_in' AND name='nil_rated_group'))
                    ) IS NOT NULL 
                        THEN ABS(aml.balance)
                        ELSE 0
                    END) AS nil_rated_amount,

                    (CASE WHEN (
                        SELECT MAX(account_tax_id) FROM account_move_line_account_tax_rel
                            JOIN account_tax at ON at.id = account_tax_id
                            WHERE account_move_line_id = aml.id AND at.tax_group_id IN 
                             ((SELECT res_id FROM ir_model_data WHERE module='l10n_in' AND name='exempt_group'))
                    ) IS NOT NULL 
                        THEN ABS(aml.balance)
                        ELSE 0
                    END) AS exempted_amount,

                    (CASE WHEN (
                        SELECT MAX(account_tax_id) FROM account_move_line_account_tax_rel
                            WHERE account_move_line_id = aml.id
                        ) IS NULL 
                        THEN ABS(aml.balance)
                        ELSE 0
                    END) AS non_gst_supplies

                FROM account_move_line aml
                    JOIN account_move am ON am.id = aml.move_id
                    JOIN account_account aa ON aa.id = aml.account_id
                    JOIN account_journal aj ON aj.id = am.journal_id
                    LEFT JOIN res_partner p ON p.id = am.partner_id
                    LEFT JOIN res_country pc ON pc.id = p.country_id
                    LEFT JOIN res_partner gstin_p ON gstin_p.id = am.l10n_in_gstin_partner_id
                WHERE aa.internal_type = 'other' and aml.tax_line_id IS NULL
            )""" % (self._table))
