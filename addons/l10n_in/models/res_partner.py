# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    l10n_in_supply_type = fields.Selection([
        ('inter_state', 'Inter State'),
        ('export_import', 'Export/Import')], string="Supply Type")

    @api.model
    def _get_fpos_by_region(self, country_id=False, state_id=False, zipcode=False, vat_required=False):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        if self.env['res.company'].browse(company_id).country_id.code == 'IN':
            return False

    @api.model
    def get_fiscal_position(self, partner_id, delivery_id=None):
        fiscal_position_id = super(AccountFiscalPosition, self).get_fiscal_position(partner_id=partner_id, delivery_id=delivery_id)
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        if self.env['res.company'].browse(company_id).country_id.code != 'IN' or fiscal_position_id:
            return fiscal_position_id
        l10n_in_gstin_partner_id = self.env.context.get('l10n_in_gstin_partner_id')
        if l10n_in_gstin_partner_id and partner_id:
            partner_id = self.env['res.partner'].browse(partner_id)
            gstin_partner_id = self.env['res.partner'].browse(l10n_in_gstin_partner_id)
            supply_type = False
            if partner_id.state_id.id != gstin_partner_id.state_id.id:
                supply_type = 'inter_state'
            if partner_id.country_id.id != gstin_partner_id.country_id.id:
                supply_type = 'export_import'
            if supply_type:
                fiscal_position_id = self.search([
                    ('company_id', '=', company_id),
                    ('auto_apply', '=', True),
                    ('l10n_in_supply_type', '=', supply_type)], limit=1)
        return fiscal_position_id.id if fiscal_position_id else False


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #Use for Multi GSTIN
    l10n_in_gstin_company_id = fields.Many2one('res.company', string="GSTIN Company")
    #Use in view attrs. Need to required state_id if Country is India.
    country_code = fields.Char(related="country_id.code", string="Country code")
    #In GSTR-2 report We need to specify that vendor is under composition scheme or not.
    l10n_in_composition = fields.Boolean(string="Is Composition", help="Check this box if this vendor is under composition scheme")

    @api.multi
    def name_get(self):
        res = super(ResPartner, self).name_get()
        if not self._context.get('show_vat'):
            return res
        new_res = []
        for partner in res:
            name = partner[1]
            vat = self.browse(partner[0]).vat
            if vat:
                name = "%s (%s)" % (name, vat)
            new_res.append((partner[0], name))
        return new_res

    @api.constrains('vat')
    def l10n_in_check_vat(self):
        for partner in self.filtered(lambda p: p.vat):
            country_code = partner.commercial_partner_id.country_id.code
            if country_code == 'IN':
                if len(partner.vat) != 15:
                    msg = _('The GSTIN [%s] for partner [%s] should be 15 characters only.') % (self.vat, self.name)
                    raise ValidationError(msg)
