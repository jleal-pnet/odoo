# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #Use for Multi GSTIN
    l10n_in_gstin_company_id = fields.Many2one('res.company', string="GSTIN Company")
    #Use in view attrs. Need to required state_id if Country is India.
    country_code = fields.Char(related="country_id.code", string="Country code")
    #In GSTR-2 report We need to specify that vendor is under composition scheme or not.
    l10n_in_composition = fields.Boolean(string="Is Composition", help="Check this box if this vendor is under composition scheme")
