# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes', digits=0, store=True)
    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=0, store=True)
    amount_paid = fields.Float(compute='_compute_amount_all', string='Paid', digits=0, store=True)
    amount_return = fields.Float(compute='_compute_amount_all', string='Returned', digits=0, store=True)

    @api.model
    def _get_account_move_line_group_data_type_key(self, data_type, values):
        res = super(PosOrder, self)._get_account_move_line_group_data_type_key(data_type, values)
        if data_type == 'product' and res:
            return res + (values['l10n_in_pos_order_id'],)
        return res

    def _prepare_move_line(self, line, partner_id, current_company, cur):
        res = super(PosOrder, self)._prepare_move_line(line, partner_id, current_company, cur)
        for line_values in res:
            if line_values.get('data_type') == 'product':
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                line_values['values'].update({
                    'l10n_in_tax_price_unit': price,
                    'l10n_in_pos_order_id': line.order_id.id
                    })
        return res

    @api.multi
    def _create_account_move_line(self, session=None, move=None):
        """When create account move and payment from pos order then update l10n_in_gstin_partner_id value from pos.config"""
        res = super(PosOrder, self)._create_account_move_line(session=session, move=move)
        for order in self:
            l10n_in_gstin_partner_id = order.config_id.l10n_in_gstin_partner_id.id
            if order.account_move:
                order.account_move.write({'l10n_in_gstin_partner_id': l10n_in_gstin_partner_id})
            payment = self.env['account.payment']
            move = self.env['account.move']
            for statement_line_id in order.statement_ids:
                for journal_entry_id in statement_line_id.journal_entry_ids:
                    if journal_entry_id.move_id not in move:
                        move += journal_entry_id.move_id
                    if journal_entry_id.payment_id not in payment:
                        payment += journal_entry_id.payment_id
            move.write({'l10n_in_gstin_partner_id': l10n_in_gstin_partner_id})
            payment.write({'l10n_in_gstin_partner_id': l10n_in_gstin_partner_id})
        return res

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        res['l10n_in_gstin_partner_id'] = self.config_id.l10n_in_gstin_partner_id.id
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal w/o Tax', store=True)
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal', store=True)
