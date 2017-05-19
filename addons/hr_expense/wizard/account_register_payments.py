# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug import url_encode
from odoo import api, fields, models, _


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    expense_sheet_id = fields.Many2one('hr.expense.sheet')

    @api.model
    def default_get(self, fields):
        vals = super(AccountRegisterPayments, self).default_get(fields)
        if not vals.get('expense_sheet_id'):
            return vals
        expense_sheet = self.env['hr.expense.sheet'].browse(vals.get('expense_sheet_id'))
        partner = expense_sheet.address_id or expense_sheet.employee_id.address_home_id
        total_amount = self._compute_payment_amount(expense_sheet=expense_sheet, currency=expense_sheet.currency_id)
        vals.update(
            partner_type='supplier',
            payment_type='outbound',
            amount=abs(total_amount),
            currency_id=expense_sheet.currency_id.id,
            partner_id=partner.id
        )
        return vals

    @api.multi
    def _compute_payment_amount(self, invoices=None, expense_sheet=None, currency=None):
        if expense_sheet or self.expense_sheet_id:
            return self._compute_payment_amount_for_expense_sheet(expense_sheet=expense_sheet, currency=currency)
        else:
            return super(AccountRegisterPayments, self)._compute_payment_amount(invoices=invoices, currency=currency)

    @api.multi
    def _compute_payment_amount_for_expense_sheet(self, expense_sheet=None, currency=None):
        '''Compute the total amount for the payment wizard.

        :param expense_sheet: If not specified, it will pick current expense.
        :param currency: If not specified, search a default currency on wizard/journal.
        :return: The total amount to pay the expense.
        '''
        if not expense_sheet:
            expense_sheet = self.expense_sheet_id
        if not currency:
            currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id
        if expense_sheet.currency_id == currency:
            total = expense_sheet.total_amount
        else:
            total = expense_sheet.currency_id.with_context(date=self.payment_date).compute(expense_sheet.total_amount, currency)
        return total

    @api.multi
    def _prepare_expense_payment_vals(self):
        partner = self.expense_sheet_id.address_id or self.expense_sheet_id.employee_id.address_home_id
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'amount': abs(self.amount),
            'currency_id': self.expense_sheet_id.currency_id.id,
            'partner_id': partner.id
        }

    @api.multi
    def get_payments_vals(self):
        if not self.expense_sheet_id:
            return super(AccountRegisterPayments, self).get_payments_vals()
        return [self._prepare_expense_payment_vals()]

    def _create_payments(self):
        payment = super(AccountRegisterPayments, self)._create_payments()

        if not self.expense_sheet_id:
            return payment

        # Log the payment in the chatter
        msg = _("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense <i>%s</i> has been made.")
        body = (msg % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, self.expense_sheet_id.name))
        self.expense_sheet_id.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + self.expense_sheet_id.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable':
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()
        return payment

    @api.multi
    def create_payments(self):
        res = super(AccountRegisterPayments, self).create_payments()
        if not self.expense_sheet_id:
            return res
        # When expense is paid, unlike invoice payments, we do not want to open the Payment that was created, hence closing the payment wizard.
        return {'type': 'ir.actions.act_window_close'}
