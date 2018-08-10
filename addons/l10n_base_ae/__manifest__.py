# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'United Arab Emirates base localization',
    'category': 'Localization',
    'description': """This module allows us to load country specific data that are used for specific localization
like countries, country states or country-related information that are not related to accounting.
""",
    'data': ['data/res.country.state.csv'],
    'post_init_hook': '_l10_base_country_install',
}
