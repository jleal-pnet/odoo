# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import report

from odoo import api, SUPERUSER_ID

def _create_buy_rules(cr, registry):

    env = api.Environment(cr, SUPERUSER_ID, {})
    warehouse_ids = env['stock.warehouse'].search([])
    for warehouse_id in warehouse_ids:
        warehouse_id.buy_pull_id = warehouse_id._update_buy_rule()
