# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        if self.company_id.anglo_saxon_accounting and self.type in ('out_invoice', 'out_refund'):
            for i_line in self.invoice_line_ids:
                res.extend(self._anglo_saxon_sale_move_lines(i_line))
        return res

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        """Return the additional move lines for sales invoices and refunds.

        i_line: An account.invoice.line object.
        res: The move line entries produced so far by the parent move_line_get.
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id
        price_unit = i_line._get_anglo_saxon_price_unit()
        if inv.currency_id != company_currency:
            currency = inv.currency_id
            amount_currency = i_line._get_price(company_currency, price_unit)
        else:
            currency = False
            amount_currency = False

        return self.env['product.product']._anglo_saxon_sale_move_lines(i_line.name, i_line.product_id, i_line.uom_id, i_line.quantity, price_unit, currency=currency, amount_currency=amount_currency, fiscal_position=inv.fiscal_position_id, account_analytic=i_line.account_analytic_id, analytic_tags=i_line.analytic_tag_ids)

    def _get_related_stock_moves(self): #TODO OCO à overrider
        """ To be overridden for customer invoices and vendor bills in order to
        return the stock moves related to this invoice.
        """
        return self.env['stock.move']

    def _get_products_set(self):
        """ Returns a recordset of the products contained in this invoice's lines
        """
        return self.mapped('invoice_line_ids.product_id')

    def _get_anglosaxon_interim_account(self, product):
        """ Returns the interim account used in anglosaxon accounting for
        this invoice"""
        if self.type in ('out_invoice', 'out_refund'):
            return product.product_tmpl_id._get_product_accounts()['stock_output']
        elif self.type in ('in_invoice', 'in_refund'):
            return product.product_tmpl_id.get_product_accounts()['stock_input']

        return None

    def invoice_validate(self):
        super(AccountInvoice, self).invoice_validate()
        self.anglo_saxon_reconcile_valuation()

    def anglo_saxon_reconcile_valuation(self, equalize_interim_writings=False): #TODO OCO setter le paramètre à true dans stock.py (ATTENTION: c'est seulement cool quand on livre tout d'un coup :/ Il faudrait un genre de garde-fou si jamais il n'y a qu'une partie des produits qui est concernée ... Il va sans doute falloir bouger tout sur les stock moves quand même ... :/) ==> Risque d'être tendu :/ :> Si ça s'avère impossible, ne faire ça que quand le stock move achève la livraison (et uniquement sur les SO !!!)
        """ Reconciles the entries made in the interim accounts in anglosaxon accounting,
        reconciling stock valuation move lines with the invoice's.
        """
        company_currency = invoice.company_id.currency_id
        for invoice in self:
            if invoice.company_id.anglo_saxon_accounting:
                invoice_stock_moves_id_list = self._get_related_stock_moves().ids
                for product in self._get_products_set():
                    if product.valuation == 'real_time' and product.cost_method == 'fifo':
                        # We first get the invoice's move lines ...
                        product_interim_account = invoice._get_anglosaxon_interim_account(product)
                        to_reconcile = self.env['account.move.line'].search([('move_id','=',invoice.move_id.id), ('product_id','=',product.id), ('account_id','=',product_interim_account.id), ('reconciled','=',False)])

                        # And then the stock valuation ones.
                        product_stock_moves = self.env['stock.move'].search([('id','in',invoice_stock_moves_id_list), ('product_id','=',product.id)])

                        for valuation_line in product_stock_moves.mapped('account_move_ids.line_ids'):
                            if valuation_line.account_id == product_interim_account and not valuation_line.reconciled:
                                to_reconcile += valuation_line

                        if to_reconcile:

                            if equalize_interim_writings: #TODO OCO nettoyer
                                balance = company_currency.round(sum(to_reconcile.mapped('balance')))
                                if not company_currency.is_zero(balance):
                                    #équilibrer avec une ligne sur le journal de stock.
                                    #Je me demande si refaire carrément un account move pour la rectification n'est pas plus judicieux ...

                            to_reconcile.reconcile()


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def _get_anglo_saxon_price_unit(self):
        self.ensure_one()
        return self.product_id._get_anglo_saxon_price_unit(uom=self.uom_id)

    def _get_price(self, company_currency, price_unit):
        if self.invoice_id.currency_id.id != company_currency.id:
            price = company_currency.with_context(date=self.invoice_id.date_invoice).compute(price_unit * self.quantity, self.invoice_id.currency_id)
        else:
            price = price_unit * self.quantity
        return self.invoice_id.currency_id.round(price)

    def get_invoice_line_account(self, type, product, fpos, company):
        if company.anglo_saxon_accounting and type in ('in_invoice', 'in_refund') and product and product.type == 'product':
            accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)
            if accounts['stock_input']:
                return accounts['stock_input']
        return super(AccountInvoiceLine, self).get_invoice_line_account(type, product, fpos, company)
