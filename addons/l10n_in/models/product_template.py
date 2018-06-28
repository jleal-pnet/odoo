# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_in_hsn_code = fields.Char(string="HSN/SAC Code", help="Harmonized System Nomenclature/Services Accounting Code")
    l10n_in_hsn_description = fields.Char(string="HSN/SAC Description", help="HSN/SAC description is required if HSN/SAC code is not provided.")
    l10n_in_is_eligible_for_itc = fields.Boolean(string="Is eligible for ITC",  help="Check this box if this product is eligible for ITC(Input Tax Credit) under GST")
    l10n_in_is_asset = fields.Boolean(string="Is Asset", help="Check this box if this product is asset")
