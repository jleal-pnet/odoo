# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('warehouse_id')
    def _onchange_l10n_in_sale_stock_warehouse_id(self):
        self.l10n_in_gstin_partner_id = self.warehouse_id and self.warehouse_id.partner_id.id or self.company_id.partner_id.id
