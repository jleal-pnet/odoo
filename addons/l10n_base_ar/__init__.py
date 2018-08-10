# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, SUPERUSER_ID

def _l10_base_country_install(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    country = env['res.country'].search([('code', '=', 'AR')])
    country.is_l10_base_install = True
