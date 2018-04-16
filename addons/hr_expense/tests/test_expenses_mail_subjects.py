# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


class TestExpenseSubject(TestExpenseCommon):
    """
    Check subject parsing while registering expense via mail.
    """

    def setUp(self):
        super(TestExpenseSubject, self).setUp()
        self.product_expense = self.env['product.product'].create({
            'name': "Phone bill",
            'can_be_expensed': True,
            'standard_price': 700,
            'list_price': 700,
            'type': 'consu',
            'default_code': 'EXP-PHONE'
        })

    def test_expense_subjects(self):
        employee = self.employee
        employee.user_id = self.user_employee
        default_expense_product = self.env.ref('hr_expense.product_product_fixed_cost')
        parse_subject = self.env['hr.expense']._parse_expense_subject
        company_currency = employee.company_id.currency_id
        alternate_currency = self.env['res.currency'].search([('id', '!=', company_currency.id)], limit=1)

        # Without Multi currency access
        subject = 'foo [EXP-PHONE] bar %s1205.91 electro wizard' % (company_currency.symbol,)  # subject with product code in []
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar electro wizard', "Should be remove price and product from subject")
        self.assertAlmostEquals(vals['unit_amount'], 1205.91, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        subject = 'EXP-PHONE foo bar %s 2910.94 minion horde' % (company_currency.name,)  # subject with product code at start
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar minion horde', "Should be remove price and product from subject")
        self.assertAlmostEquals(vals['unit_amount'], 2910.94, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # subject having other currency then company currency, it should ignore other currency then company currency
        subject = 'foo bar [EXP-PHONE] %s1406.91 royal giant' % (alternate_currency.symbol,)
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar %s royal giant' % (alternate_currency.symbol,), "Should be remove price and product from subject but not currency symbol")
        self.assertAlmostEquals(vals['unit_amount'], 1406.91, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # With Multi currency access
        group_multi_currency = self.env.ref('base.group_multi_currency')
        self.user_employee.write({
            'groups_id': [(4, group_multi_currency.id)],
        })

        subject = '[Phone bill] foo bar %s2205.92 elite barbarians' % (company_currency.symbol,)  # with product name in []
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar elite barbarians', "Should be remove price and product from subject")
        self.assertAlmostEquals(vals['unit_amount'], 2205.92, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # subject having other currency then company currency, it should accept other currency because multi currency is activated
        subject = 'foo bar [EXP-PHONE] %s2510.90 chhota bheem' % (alternate_currency.symbol,)
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar chhota bheem', "Should be remove price and product from subject but not currency symbol")
        self.assertAlmostEquals(vals['unit_amount'], 2510.90, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], alternate_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # subject without product and currency, should take company currency and default product
        subject = 'foo bar 109.96 spear goblins'
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar spear goblins', "Should be remove price and product from subject but not currency symbol")
        self.assertAlmostEquals(vals['unit_amount'], 109.96, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch company currency")
        self.assertEquals(vals['product_id'], default_expense_product.id, "Should fetch default product")

        # subject with currency symbol at end
        subject = 'EXP-PHONE foo bar 2910.94%s inferno dragon' % (company_currency.symbol,)
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar inferno dragon', "Should be remove price and product from subject")
        self.assertAlmostEquals(vals['unit_amount'], 2910.94, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # subject with currency code at end
        subject = 'EXP-PHONE foo bar 2910.94%s sparky' % (company_currency.name,)
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar sparky', "Should be remove price and product from subject")
        self.assertAlmostEquals(vals['unit_amount'], 2910.94, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], self.product_expense.id, "Should fetch product correctly")

        # subject with no amount and product
        subject = 'foo bar mega knight'
        vals = parse_subject(subject, employee)
        self.assertEquals(vals['name'], 'foo bar mega knight', "Should be same as subject")
        self.assertAlmostEquals(vals['unit_amount'], 0.0, "Price is not fetched correctly")
        self.assertEquals(vals['currency_id'], company_currency.id, "Should fetch currency correctly")
        self.assertEquals(vals['product_id'], default_expense_product.id, "Should fetch product correctly")
