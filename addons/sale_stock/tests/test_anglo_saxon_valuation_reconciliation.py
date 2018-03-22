# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo.addons.stock_account.tests.test_anglo_saxon_valuation_reconciliation_common import ValuationReconciliationTestCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestValuationReconciliation(ValuationReconciliationTestCase):

    def create_sale(self, product):
        rslt = self.env['sale.order'].create({
            'partner_id': self.test_partner.id,
            'currency_id': self.currency_one.id,
            'order_line': [
                (0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'qty_to_invoice': 1.0,
                    'product_uom': product.uom_po_id.id,
                    'price_unit': self.product_price_unit,
                })],
        })
        rslt.action_confirm()
        return rslt

    def create_invoice_for_so(self, sale_order, product):
        account_payable = self.env['account.account'].create({'code': 'X1111', 'name': 'Sale - Test Payable Account', 'user_type_id': self.env.ref('account.data_account_type_payable').id, 'reconcile': True})
        account_income = self.env['account.account'].create({'code': 'X1112', 'name': 'Sale - Test Account', 'user_type_id': self.env.ref('account.data_account_type_direct_costs').id})
        rslt = self.env['account.invoice'].create({
            'partner_id': self.test_partner.id,
            'reference_type': 'none',
            'currency_id': self.currency_two.id,
            'name': 'customer invoice',
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y') + '-12-22',
            'account_id': account_payable.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'test line',
                'origin': sale_order.name,
                'account_id': account_income.id,
                'price_unit': self.currency_one.compute(self.product_price_unit, self.currency_two, round=False),
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': product.uom_id.id,
                'product_id': product.id,
                'sale_line_ids': [(6, 0, [line.id for line in sale_order.order_line])],
            })],
        })

        sale_order.invoice_ids += rslt
        return rslt

    def send_so(self, sale_order):
        sale_order.picking_ids.action_confirm()
        sale_order.picking_ids.action_assign()
        for picking in sale_order.picking_ids:
            for ml in picking.move_line_ids:
                ml.qty_done = ml.product_qty
        sale_order.picking_ids.action_done()

    def set_initial_stock_for_product(self, product):
        move1 = self.env['stock.move'].create({
            'name': 'Initial stock',
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 11,
            'price_unit': 13,
        })
        move1._action_confirm()
        move1._action_assign()
        move1.move_line_ids.qty_done = 11
        move1._action_done()

    def test_shipment_invoice(self):
        """ Tests the case into which we send the goods to the customer before
        making the invoice
        """
        test_product = self.test_product_delivery
        self.set_initial_stock_for_product(test_product)

        sale_order = self.create_sale(test_product)
        self.send_so(sale_order)

        invoice = self.create_invoice_for_so(sale_order, test_product)
        self.currency_rate.rate = 9.87366352
        invoice.action_invoice_open()
        picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id)])
        self.check_reconciliation(invoice, picking)

    def test_invoice_shipment(self):
        """ Tests the case into which we make the invoice first, and then send
        the goods to our customer.
        """
        test_product = self.test_product_order
        self.set_initial_stock_for_product(test_product)

        sale_order = self.create_sale(test_product)

        invoice = self.create_invoice_for_so(sale_order, test_product)
        self.currency_rate.rate = 0.974784
        invoice.action_invoice_open()

        self.send_so(sale_order)

        picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id)])
        self.check_reconciliation(invoice, picking)
