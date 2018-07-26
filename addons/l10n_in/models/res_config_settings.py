# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_l10n_in_multi_gstin = fields.Boolean(implied_group='l10n_in.group_l10n_in_multi_gstin', string="Multiple GSTIN registered")
    show_module_l10n_in = fields.Boolean(compute='_compute_show_module_l10n_in')

    @api.depends('company_id')
    def _compute_show_module_l10n_in(self):
        self.show_module_l10n_in = self.company_id.country_id.code == 'IN'

    @api.multi
    def set_values(self):
        """update created company partner in l10n_in_gstin_partner_ids relation.
        For use in domain of l10n_in_gstin_partner_id"""
        super(ResConfigSettings, self).set_values()
        if self.group_l10n_in_multi_gstin:
            for company in self.env['res.company'].search([('country_id.code','=', 'IN')]):
                company.partner_id.write({'l10n_in_gstin_company_id': company.id})
