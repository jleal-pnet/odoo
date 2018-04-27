# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.datetime import date, relativedelta
from odoo.exceptions import UserError


class AccountAgedTrialBalance(models.TransientModel):

    _name = 'account.aged.trial.balance'
    _inherit = 'account.common.partner.report'
    _description = 'Account Aged Trial balance Report'

    period_length = fields.Integer(string='Period Length (days)', required=True, default=30)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True)
    date_from = fields.Date(default=lambda *a: date.today())

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length<=0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = date.from_string(data['form']['date_from'])

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length +1) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start,
                'start': (i!=0 and stop or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return self.env.ref('account.action_report_aged_partner_balance').with_context(landscape=True).report_action(self, data=data)
