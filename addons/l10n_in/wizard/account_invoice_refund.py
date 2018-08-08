# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    # Refund reason for credit or debite note.
    l10n_in_refund_reason_id = fields.Many2one('l10n_in.refund.reason', string= "Refund Reason")

    @api.onchange("l10n_in_refund_reason_id")
    def _onchange_l10n_in_refund_reason(self):
        if self.l10n_in_refund_reason_id:
            self.description = self.l10n_in_refund_reason_id.name

    @api.multi
    def invoice_refund(self):
        result = super(AccountInvoiceRefund, self).invoice_refund()
        if isinstance(result, dict) and result.get('domain'):
            invoices = self.env['account.invoice'].search(result['domain'])
            for refund in self:
                invoices.write({"l10n_in_refund_reason_id": refund.l10n_in_refund_reason_id.id})
        return result
