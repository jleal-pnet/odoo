# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.bus.models.bus_presence import AWAY_TIMER
from odoo.addons.bus.models.bus_presence import DISCONNECTION_TIMER


class ResPartner(models.Model):
    _inherit = 'res.partner'

    im_status = fields.Char('IM Status', compute='_compute_im_status')

    @api.multi
    def _compute_im_status(self):
        self.env.cr.execute("""
            SELECT
                U.partner_id as id,
                CASE WHEN age(now() AT TIME ZONE 'UTC', B.last_poll) > interval %s THEN 'offline'
                     WHEN age(now() AT TIME ZONE 'UTC', B.last_presence) > interval %s THEN 'away'
                     ELSE 'online'
                END as status
            FROM bus_presence B
                JOIN res_users U ON B.user_id = U.id
            WHERE U.partner_id IN %s AND U.active = 't'
        """, ("%s seconds" % DISCONNECTION_TIMER, "%s seconds" % AWAY_TIMER, tuple(self.ids)))
        res = dict(((status['id'], status['status']) for status in self.env.cr.dictfetchall()))
        for partner in self:
            partner.im_status = res.get(partner.id, 'offline')
