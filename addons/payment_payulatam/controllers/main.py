# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class PayuLatamController(http.Controller):

    @http.route('/payment/payulatam/response', type='http', auth='public', csrf=False)
    def payulatam_response(self, **post):
        """ PayUlatam."""
        _logger.info('PayUlatam: entering form_feedback with post response data %s', pprint.pformat(post))
        return_url = '/'
        if post:
            request.env['payment.transaction'].sudo().form_feedback(post, 'payulatam')
            return_url = post.pop('extra1')
        return werkzeug.utils.redirect(return_url)

    @http.route(['/payment/payulatam/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def payulatam_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        acquirer = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id')))
        if acquirer.environment == 'test' and verify_validity:
            raise ValidationError(_('Adding a new card is not possible in Test mode.'))
        if not kwargs.get('partner_id'):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        token = acquirer.s2s_process(kwargs)

        if not token:
            res = {
                'result': False,
            }
            return res

        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': False,
        }

        if verify_validity:
            token.validate(**kwargs)
            res['verified'] = token.verified

        return res
