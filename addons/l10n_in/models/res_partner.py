# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #Use for Multi GSTIN
    l10n_in_gstin_company_id = fields.Many2one('res.company', string="GSTIN Company")
