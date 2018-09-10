# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Channel(models.Model):
    _inherit = 'mail.channel'

    subscription_department_ids = fields.Many2many(
        'hr.department', string='HR Departments',
        help='Automatically subscribe members of those departments to the channel.')

    def _subscribe_users(self):
        """ Auto-subscribe members of a department to a channel """
        super(Channel, self)._subscribe_users()
        for mail_channel in self:
            if mail_channel.subscription_department_ids:
                mail_channel.write(
                    {'channel_partner_ids':
                        [(4, partner_id) for partner_id in mail_channel.mapped('subscription_department_ids.member_ids.user_id.partner_id').ids]})

    def write(self, vals):
        res = super(Channel, self).write(vals)
        if vals.get('subscription_department_ids'):
            self._subscribe_users()
        return res

    def channel_fetch_slot(self):
        values = super(Channel, self).channel_fetch_slot()
        my_partner_id = self.env.user.partner_id.id
        depChannels = self.search([('channel_type', '=', 'channel'), ('public', '=', 'department'), ('channel_partner_ids', 'in', [my_partner_id])]).channel_info()
        values['channel_private_group'].extend(depChannels)
        return values
