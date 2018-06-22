# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    #for Multi GSTIN.
    l10n_in_gstin_partner_ids = fields.One2many('res.partner', 'l10n_in_gstin_company_id', string="GST")

    @api.model
    def create(self, vals):
        """update company partner in l10n_in_gstin_partner_ids relation.
        For use in domain of l10n_in_gstin_partner_id.
        """
        company = super(ResCompany, self).create(vals)
        company.partner_id.write({'l10n_in_gstin_company_id': company.id})
        return company
