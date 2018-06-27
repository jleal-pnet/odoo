# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

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
