# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    company_data_id = fields.Integer('Company database ID', related="partner_id.company_data_id", inverse="_inverse_company_data_id", store=True)

    def _inverse_company_data_id(self):
        for company in self:
            company.partner_id.company_data_id = company.company_data_id
