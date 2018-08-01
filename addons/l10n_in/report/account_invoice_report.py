# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class L10nInAccountInvoiceReport(models.Model):

    _name = "l10n_in.account.invoice.report"
    _description = "Account Invoice Statistics"
    _auto = False
    _order = 'date desc'

    account_move_id = fields.Many2one('account.move', string="Account Move")
    account_move_line_id = fields.Many2one('account.move.line', string="Account Move Line")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    company_id = fields.Many2one('res.company', string="Company")
    gstin_partner_id = fields.Many2one('res.partner', string="GSTIN")
    date = fields.Date(string="Accounting Date")
    name = fields.Char(string="Invoice Number")
    partner_id = fields.Many2one('res.partner', string="Customer")
    l10n_in_tax_id = fields.Many2one('account.tax', string="GST Tax")
    is_reverse_charge = fields.Char("Reverse Charge")
    l10n_in_export_type = fields.Selection([
        ('regular', 'Regular'), ('deemed', 'Deemed'),
        ('sale_from_bonded_wh', 'Sale from Bonded WH'),
        ('export_with_igst', 'Export with IGST'),
        ('sez_with_igst', 'SEZ with IGST payment'),
        ('sez_without_igst', 'SEZ without IGST payment')])
    journal_id = fields.Many2one('account.journal', string="Journal")
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status')
    igst_amount = fields.Float(string="IGST Amount")
    cgst_amount = fields.Float(string="CGST Amount")
    sgst_amount = fields.Float(string="SGST Amount")
    cess_amount = fields.Float(string="Cess Amount")
    price_total = fields.Float(string='Total Without Tax')
    total = fields.Float(string="Invoice Total")
    refund_reason_id = fields.Many2one('l10n_in.refund.reason', string="Refund Reason")
    refund_invoice_id = fields.Many2one('account.invoice', string="Refund Invoice", help="From where this Refund is created")
    shipping_bill_number = fields.Char(string="Shipping Bill Number")
    shipping_bill_date = fields.Date(string="Shipping Bill Date")
    shipping_port_code_id = fields.Many2one('l10n_in.port.code', string='Shipping port code')
    ecommerce_partner_id = fields.Many2one('res.partner', string="E-commerce")
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
        ])
    l10n_in_place_of_supply = fields.Many2one("res.country.state", String="Customer State")
    partner_vat = fields.Char(string="Customer GSTIN")
    ecommerce_vat = fields.Char(string="E-commerce GSTIN")
    l10n_in_description = fields.Char(string="Rate")
    place_of_supply = fields.Char(string="Place of Supply")
    is_pre_gst = fields.Char(string="Is Pre GST")
    is_ecommerce = fields.Char(string="Is E-commerce")
    b2cl_is_ecommerce = fields.Char(string="B2CL Is E-commerce")
    b2cs_is_ecommerce = fields.Char(string="B2CS Is E-commerce")
    supply_type = fields.Char(string="Supply Type")
    export_type = fields.Char(string="Export Type")  # String from GSTR column.
    refund_export_type = fields.Char(string="UR Type")  # String from GSTR column.
    b2b_type = fields.Char(string="B2B Invoice Type")
    refund_invoice_type = fields.Char(string="Document Type")
    gst_format_date = fields.Char(string="Formated Date")
    gst_format_refund_date = fields.Char(string="Formated Refund Date")
    gst_format_shipping_bill_date = fields.Char(string="Formated Shipping Bill Date")

    def _select(self):
        select_str = """
            SELECT concat(am.id, '-', aml.l10n_in_tax_id, '-', aml.partner_id) AS id,
                min(aml.id) AS account_move_line_id,
                aml.invoice_id,
                aml.l10n_in_tax_id,
                am.id AS account_move_id,
                am.name,
                am.state,
                aml.partner_id,
                am.date,
                am.l10n_in_export_type AS l10n_in_export_type,
                am.l10n_in_gstin_partner_id AS gstin_partner_id,
                am.l10n_in_reseller_partner_id AS ecommerce_partner_id,
                am.l10n_in_shipping_bill_number AS shipping_bill_number,
                am.l10n_in_shipping_bill_date AS shipping_bill_date,
                am.l10n_in_shipping_port_code_id AS shipping_port_code_id,
                am.amount AS total,
                am.journal_id,
                aj.company_id,
                ai.type AS invoice_type,
                ai.refund_invoice_id AS refund_invoice_id,
                ai.l10n_in_refund_reason_id AS refund_reason_id,
                am.l10n_in_place_of_supply,
                p.vat AS partner_vat,
                rp.vat AS ecommerce_vat,
                at.l10n_in_description,
                sum(aml.l10n_in_igst_amount) AS igst_amount,
                sum(aml.l10n_in_cgst_amount) AS cgst_amount,
                sum(aml.l10n_in_sgst_amount) AS sgst_amount,
                sum(aml.l10n_in_cess_amount) AS cess_amount,
                sum(ABS(aml.balance)) AS price_total,
                (CASE WHEN am.l10n_in_reverse_charge = True
                    THEN 'Y'
                    ELSE 'N'
                    END)  AS is_reverse_charge,
                (CASE WHEN pos.l10n_in_tin IS NOT NULL
                    THEN concat(pos.l10n_in_tin,'-',pos.name)
                    ELSE ''
                    END) AS place_of_supply,
                (CASE WHEN ai.type in ('out_refund', 'in_refund') and refund_ai.date <= to_date('2017-07-01', 'YYYY-MM-DD')
                    THEN 'Y'
                    ELSE 'N'
                    END) as is_pre_gst,

                (CASE WHEN am.l10n_in_reseller_partner_id IS NOT NULL
                    THEN 'Y'
                    ELSE 'N'
                    END) as is_ecommerce,
                (CASE WHEN am.l10n_in_reseller_partner_id IS NOT NULL
                    THEN 'Y'
                    ELSE 'N'
                    END) as b2cl_is_ecommerce,
                (CASE WHEN am.l10n_in_reseller_partner_id IS NOT NULL
                    THEN 'E'
                    ELSE 'OE'
                    END) as b2cs_is_ecommerce,
                (CASE WHEN pos.id = gstin_ps.id
                    THEN 'Intra State'
                    WHEN pos.id != gstin_ps.id
                    THEN 'Inter State'
                    END) AS supply_type,
                (CASE WHEN am.l10n_in_export_type in ('deemed', 'export_with_igst', 'sez_with_igst')
                    THEN 'EXPWP'
                    WHEN am.l10n_in_export_type in ('sale_from_bonded_wh', 'sez_without_igst')
                    THEN 'EXPWOP'
                    ELSE ''
                    END) AS export_type,
                (CASE WHEN refund_ai.l10n_in_export_type in ('deemed', 'export_with_igst', 'sez_with_igst')
                    THEN 'EXPWP'
                    WHEN refund_ai.l10n_in_export_type in ('sale_from_bonded_wh', 'sez_without_igst')
                    THEN 'EXPWOP'
                    ELSE 'B2CL'
                    END) AS refund_export_type,
                (CASE WHEN ai.l10n_in_export_type = 'regular'
                    THEN 'Regular'
                    WHEN ai.l10n_in_export_type = 'deemed'
                    THEN 'Deemed'
                    WHEN ai.l10n_in_export_type = 'sale_from_bonded_wh'
                    THEN 'Sale from Bonded WH'
                    WHEN ai.l10n_in_export_type = 'export_with_igst'
                    THEN 'Export with IGST'
                    WHEN ai.l10n_in_export_type = 'sez_with_igst'
                    THEN 'SEZ with IGST payment'
                    WHEN ai.l10n_in_export_type = 'sez_without_igst'
                    THEN 'SEZ without IGST payment'
                    END) AS b2b_type,
                (CASE WHEN ai.type = 'out_refund'
                    THEN 'C'
                    WHEN ai.type = 'in_refund'
                    THEN 'D'
                    ELSE ''
                    END) as refund_invoice_type,
                (CASE WHEN am.date IS NOT NULL
                    THEN TO_CHAR(am.date, 'DD-MON-YYYY')
                    ELSE ''
                    END) as gst_format_date,
                (CASE WHEN refund_ai.date IS NOT NULL
                    THEN TO_CHAR(refund_ai.date, 'DD-MON-YYYY')
                    ELSE ''
                    END) as gst_format_refund_date,
                (CASE WHEN am.l10n_in_shipping_bill_date IS NOT NULL
                    THEN TO_CHAR(am.l10n_in_shipping_bill_date, 'DD-MON-YYYY')
                    ELSE ''
                    END) as gst_format_shipping_bill_date

        """
        return select_str

    def _from(self):
        from_str = """
            FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN account_journal aj ON aj.id = am.journal_id
                LEFT JOIN account_invoice ai ON ai.id = aml.invoice_id
                LEFT JOIN account_invoice refund_ai ON refund_ai.id = ai.refund_invoice_id
                LEFT JOIN res_partner p ON p.id = aml.partner_id
                LEFT JOIN res_country_state pos ON pos.id = am.l10n_in_place_of_supply
                LEFT JOIN res_partner gstin_p ON gstin_p.id = am.l10n_in_gstin_partner_id
                LEFT JOIN res_country_state gstin_ps ON gstin_ps.id = gstin_p.state_id
                LEFT JOIN res_partner rp ON rp.id = am.l10n_in_reseller_partner_id
                LEFT JOIN account_tax at ON at.id = aml.l10n_in_tax_id
                where am.state = 'posted' AND aml.l10n_in_tax_id IS NOT NULL
                    AND at.tax_group_id not in (SELECT res_id FROM ir_model_data WHERE module='l10n_in' AND name in ('exempt_group','nil_rated_group'))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
        GROUP BY
            am.id,
            aj.company_id,
            aml.invoice_id,
            am.name,
            am.state,
            aml.partner_id,
            aml.l10n_in_tax_id,
            am.date,
            am.l10n_in_reverse_charge,
            am.l10n_in_export_type,
            am.l10n_in_gstin_partner_id,
            am.l10n_in_reseller_partner_id,
            am.l10n_in_shipping_bill_number,
            am.l10n_in_shipping_bill_date,
            am.l10n_in_shipping_port_code_id,
            am.amount,
            am.journal_id,
            am.company_id,
            ai.type,
            ai.refund_invoice_id,
            ai.l10n_in_refund_reason_id,
            am.l10n_in_place_of_supply,
            p.vat,
            rp.vat,
            at.l10n_in_description,
            pos.l10n_in_tin,
            pos.name,
            p.id,
            gstin_ps.l10n_in_tin,
            gstin_ps.name,
            refund_ai.date,
            pos.id,
            gstin_ps.id,
            refund_ai.l10n_in_export_type,
            ai.l10n_in_export_type
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
            %s %s %s)""" % (self._table, self._select(), self._from(), self._group_by()))
