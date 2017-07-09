# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'VAT Number Autocomplete',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
Auto-Complete Addresses based on VAT numbers
============================================

    """,
    'depends': ['base_vat'],
    'website': 'https://www.odoo.com/page/accounting',
    'data': [
        'views/res_partner_views.xml',
    ],
    'auto_install': True
}
