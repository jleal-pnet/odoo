# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Indian - Sales and Warehouse Management',
    'version': '1.0',
    'description': """GST Quotation, Sales Orders, Delivery""",
    'category': 'Localization',
    'depends': [
        'l10n_in',
        'sale',
        'stock'
    ],
    'data': [
        'views/sale_views.xml'
    ],
    'auto_install': True,
}
