# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_be_edi = fields.Boolean(string='E-Invoicing (Belgium)')
