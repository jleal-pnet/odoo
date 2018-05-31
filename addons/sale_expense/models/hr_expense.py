# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Expense(models.Model):
    _inherit = "hr.expense"

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)]}, domain=[('state', '=', 'sale')])

    @api.model
    def create(self, values):
        if values.get('sale_order_id') and not values.get('analytic_account_id'):
            sale_order = self.env['sale.order'].sudo().browse(values['sale_order_id'])
            if sale_order.analytic_account_id:
                values['analytic_account_id'] = sale_order.analytic_account_id.id
        return super(Expense, self).create(values)

    @api.multi
    def write(self, values):
        """ When changing the SO, we want the expense to be reinvoice throught the analytic account
            of it, so we don't have to check if any record in `self` has the analytic_account set, we
            simply force the change.
        """
        if values.get('sale_order_id') and not values.get('analytic_account_id'):
            sale_order = self.env['sale.order'].sudo().browse(values['sale_order_id'])
            if sale_order.analytic_account_id:
                values['analytic_account_id'] = sale_order.analytic_account_id.id
        return super(Expense, self).write(values)

    @api.multi
    def action_move_create(self):
        """ When posting expense, if a SO is set, this means you want to reinvoice. To do so, we
            have to set an Analytic Account on the expense. We choose the one from the SO, and
            if it does not exist, we generate it. Create AA even for product with no expense policy
            to keep track of the analytic.
        """
        for expense in self.filtered(lambda expense: expense.sale_order_id and not expense.analytic_account_id):
            if not expense.sale_order_id.analytic_account_id:
                expense.sale_order_id._create_analytic_account()
            expense.write({
                'analytic_account_id': expense.sale_order_id.analytic_account_id.id
            })
        return super(Expense, self).action_move_create()
