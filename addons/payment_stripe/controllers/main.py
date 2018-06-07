# -*- coding: utf-8 -*-
import json
import logging
import pprint
import requests
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class StripeController(http.Controller):

    def _stripe_validate_data(self, acquirer_id, **kwargs):
        acquirer = request.env['payment.acquirer'].browse(int(acquirer_id)).sudo()
        url = acquirer.get_stripe_url() + "/sources/" + kwargs.get('source')
        headers = {'AUTHORIZATION': 'Bearer %s' % acquirer.stripe_secret_key}
        resp = requests.post(url, headers=headers)
        data = json.loads(resp.text)
        if data.get('status') == 'chargeable':
            data = request.env['payment.transaction'].sudo().do_stripe_payment(**data)
        _logger.info('Stripe: entering form_feedback with post data %s' % pprint.pformat(data))
        return_url = "/"
        if data:
            request.env['payment.transaction'].sudo().form_feedback(data, 'stripe')
            return_url = data.get('metadata').get('return_url')
        return return_url

    @http.route(['/stripe/payment/noneflow/'], type='json', auth='public')
    def stripe_payment(self, **kwargs):
        transaction = request.env['payment.transaction'].sudo().search([('reference', '=', kwargs.get('metadata[reference]'))])
        if not transaction:
            return "/"
        return transaction.do_stripe_payment(**kwargs)

    @http.route(['/payment/stripe/return'], type='http', auth='public')
    def stripe_return(self, acquirer_id=False, **kwargs):
        _logger.info('Stripe: return with post data %s' % pprint.pformat(kwargs))
        return werkzeug.utils.redirect(self._stripe_validate_data(acquirer_id, **kwargs))

    @http.route(['/payment/stripe/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def stripe_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        if not kwargs.get('partner_id'):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        token = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id'))).s2s_process(kwargs)

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

        if verify_validity != False:
            token.validate()
            res['verified'] = token.verified

        return res
