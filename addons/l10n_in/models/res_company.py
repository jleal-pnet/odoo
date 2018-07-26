# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    #for Multi GSTIN.
    l10n_in_country_code = fields.Char(string="Country code", related='country_id.code')
    l10n_in_gstin_partner_ids = fields.One2many('res.partner', 'l10n_in_gstin_company_id', string="GST")
