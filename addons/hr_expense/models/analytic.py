# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    analytic_source = fields.Selection(selection_add=[('expense', 'Employee Expense')])
