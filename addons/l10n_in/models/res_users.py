# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    has_group_l10n_in_multi_gstin = fields.Boolean(
        'Show Multiple GSTIN', compute='_compute_groups_id', inverse='_inverse_groups_id',
        group_xml_id='l10n_in.group_l10n_in_multi_gstin')
    has_group_l10n_in_reseller = fields.Boolean(
        'Manage Reseller(E-Commerce)', compute='_compute_groups_id', inverse='_inverse_groups_id',
        group_xml_id='l10n_in.group_l10n_in_reseller')
