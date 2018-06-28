# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for invoice in self:
            invoice.amount_total_words = invoice.currency_id.amount_to_text(invoice.amount_total)

    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")
    #Use for invisible fields in form views.
    l10n_in_import_export = fields.Boolean(related='journal_id.l10n_in_import_export', readonly=True)
    #For Export invoice this data is need in GSTR report
    l10n_in_export_type = fields.Selection([
        ('regular', 'Regular'), ('deemed', 'Deemed'),
        ('sale_from_bonded_wh', 'Sale from Bonded WH'),
        ('export_with_igst', 'Export with IGST'),
        ('sez_with_igst', 'SEZ with IGST payment'),
        ('sez_without_igst', 'SEZ without IGST payment')],
        string='Export Type', default='regular', required=True)
    l10n_in_shipping_bill_number = fields.Char('Shipping bill number', readonly=True, states={'draft': [('readonly', False)]})
    l10n_in_shipping_bill_date = fields.Date('Shipping bill date', readonly=True, states={'draft': [('readonly', False)]})
    l10n_in_shipping_port_code_id = fields.Many2one('l10n_in.port.code', 'Shipping port code', states={'draft': [('readonly', False)]})
    l10n_in_reseller_partner_id = fields.Many2one('res.partner', 'Reseller', domain=[('vat', '!=', False)], help="Only Registered Reseller", readonly=True, states={'draft': [('readonly', False)]})
    l10n_in_reverse_charge = fields.Boolean('Reverse Charge', readonly=True, states={'draft': [('readonly', False)]})
    l10n_in_gstin_partner_id = fields.Many2one(
        'res.partner',
        string="GSTIN",
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.invoice').partner_id,
        readonly=True, states={'draft': [('readonly', False)]}
        )
    l10n_in_refund_reason_id = fields.Many2one('l10n_in.refund.reason', string="Refund Reason")
    l10n_in_import_type = fields.Selection([
        ('regular', 'Regular'),
        ('import_goods', 'Import of Goods'),
        ('import_goods_sez', 'Import of Goods from SEZ'),
        ('import_service', 'Import of Service'),
        ('import_service_sez', 'Import of Service from SEZ')],
        string='Import Type', default='regular', required=True)

    @api.model
    def _get_refund_common_fields(self):
        """This list of fields value pass to refund invoice."""
        return super(AccountInvoice, self)._get_refund_common_fields() + [
            'l10n_in_reverse_charge',
            'l10n_in_gstin_partner_id']

    def _get_printed_report_name(self):
        self.ensure_one()
        if self.company_id.country_id.code != 'IN':
            return super(AccountInvoice, self)._get_printed_report_name()
        return self.type == 'out_invoice' and self.state == 'draft' and _('Draft %s') % (self.journal_id.name) or \
            self.type == 'out_invoice' and self.state in ('open','paid') and '%s - %s' % (self.journal_id.name, self.number) or \
            self.type == 'out_refund' and self.state == 'draft' and _('Credit Note') or \
            self.type == 'out_refund' and _('Credit Note - %s') % (self.number) or \
            self.type == 'in_invoice' and self.state == 'draft' and _('Vendor Bill') or \
            self.type == 'in_invoice' and self.state in ('open','paid') and _('Vendor Bill - %s') % (self.number) or \
            self.type == 'in_refund' and self.state == 'draft' and _('Vendor Credit Note') or \
            self.type == 'in_refund' and _('Vendor Credit Note - %s') % (self.number)

    @api.model
    def invoice_line_move_line_get(self):
        lines_res = super(AccountInvoice, self).invoice_line_move_line_get()
        for line_res in lines_res:
            line = self.env['account.invoice.line'].browse(line_res.get('invl_id'))
            line_res.update({
                'l10n_in_tax_price_unit': (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                'l10n_in_is_eligible_for_itc': line.l10n_in_is_eligible_for_itc,
                'l10n_in_itc_percentage': line.l10n_in_itc_percentage
                })
        return lines_res

    @api.model
    def line_get_convert(self, line, part):
        """Update account move line convert vals for new field value pass to account move line"""
        vals = super(AccountInvoice, self).line_get_convert(line, part)
        vals.update({
            'l10n_in_tax_price_unit': line.get('l10n_in_tax_price_unit', 0),
            'l10n_in_is_eligible_for_itc': line.get('l10n_in_is_eligible_for_itc', False),
            'l10n_in_itc_percentage': line.get('l10n_in_itc_percentage', 0)
            })
        return vals

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            vals = {
                'l10n_in_export_type': inv.l10n_in_export_type,
                'l10n_in_shipping_bill_number': inv.l10n_in_shipping_bill_number,
                'l10n_in_shipping_bill_date': inv.l10n_in_shipping_bill_date,
                'l10n_in_shipping_port_code_id': inv.l10n_in_shipping_port_code_id.id,
                'l10n_in_reseller_partner_id': inv.l10n_in_reseller_partner_id.id,
                'l10n_in_reverse_charge': inv.l10n_in_reverse_charge,
                'l10n_in_gstin_partner_id': inv.l10n_in_gstin_partner_id.id,
                'l10n_in_import_type': inv.l10n_in_import_type
                }
            inv.move_id.write(vals)
        return res

    @api.multi
    def get_taxes_values(self):
        """Update tax when Reverse charge under GST.
        reverse charge rule is GST will have to be paid directly by the receiver to the Government instead of the supplier."""
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        if self.l10n_in_reverse_charge:
            reverse_charge_tax = {}
            for val in tax_grouped.values():
                new_val = val.copy()
                tax = self.env['account.tax'].browse(val['tax_id'])
                if not tax.refund_account_id or not tax.account_id:
                    raise ValidationError(_('Cannot find a accounts for %s tax, You should configure it. \nPlease go to Account Tax under Configuration.') % tax.name)
                new_val['account_id'] = self.type in ('out_invoice', 'in_invoice') and tax.refund_account_id.id or tax.account_id.id
                key = tax.get_grouping_key(new_val)
                reverse_charge_tax[key] = new_val
                reverse_charge_tax[key]['amount'] = new_val['amount'] * -1
            tax_grouped.update(reverse_charge_tax)
        return tax_grouped

    @api.onchange('l10n_in_reverse_charge')
    def _onchange_l10n_in_reverse_charge(self):
        """For update tax_lines."""
        return self._onchange_invoice_line_ids()

    @api.onchange('company_id')
    def _onchange_l10n_in_company(self):
        self.l10n_in_gstin_partner_id = self.company_id.partner_id


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    #This tax amount show in invoice PDF report
    l10n_in_igst_amount = fields.Float(string="IGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_cgst_amount = fields.Float(string="CGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_sgst_amount = fields.Float(string="SGST Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_cess_amount = fields.Float(string="CESS Amount", compute='_compute_l10n_in_taxes_amount', store=True, readonly=True)
    l10n_in_is_eligible_for_itc = fields.Boolean(string="Is eligible for ITC", help="Check this box if this product is eligible for ITC(Input Tax Credit) under GST")
    l10n_in_itc_percentage = fields.Float(string="ITC percentage", help="Enter percentage in case of partly eligible for ITC(Input Tax Credit) under GST.")

    @api.constrains('l10n_in_itc_percentage')
    def _check_l10n_in_itc_percentage(self):
        for record in self:
            if record.l10n_in_itc_percentage < 0 or record.l10n_in_itc_percentage > 100:
                ValidationError(_("ITC percentage between 0 to 100"))

    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_l10n_in_taxes_amount(self):
        AccountMoveLine = self.env['account.move.line']
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes_data = AccountMoveLine._compute_l10n_in_tax(
                taxes=line.invoice_line_tax_ids,
                price_unit=price,
                currency=line.invoice_id.currency_id or None,
                quantity=line.quantity,
                product=line.product_id or None,
                partner=line.invoice_id.partner_id or None)
            line.l10n_in_igst_amount = taxes_data['igst_amount']
            line.l10n_in_cgst_amount = taxes_data['cgst_amount']
            line.l10n_in_sgst_amount = taxes_data['sgst_amount']
            line.l10n_in_cess_amount = taxes_data['cess_amount']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        self.l10n_in_is_eligible_for_itc = self.product_id and self.product_id.l10n_in_is_eligible_for_itc or False
        return res
