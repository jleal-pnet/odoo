# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import pprint
import requests
import uuid

from hashlib import md5
from lxml import objectify
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)


class PaymentAcquirerPayulatam(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('payulatam', 'PayUlatam')])
    payulatam_merchant_id = fields.Char(string="PayUlatam Merchant ID", required_if_provider='payulatam', groups='base.group_user')
    payulatam_account_id = fields.Char(string="PayUlatam Account ID", required_if_provider='payulatam', groups='base.group_user')
    payulatam_api_key = fields.Char(string="PayUlatam API Key", required_if_provider='payulatam', groups='base.group_user')
    payulatam_api_login = fields.Char(string="PayUlatam API Login", required_if_provider='payulatam', groups='base.group_user')

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerPayulatam, self)._get_feature_support()
        res['tokenize'].append('payulatam')
        return res

    def _get_payulatam_urls(self, environment):
        """ PayUlatam URLs"""
        if environment == 'prod':
            return {
                'payulatam_form_url': 'https://checkout.payulatam.com/ppp-web-gateway-payu/',
                'payulatam_rest_url': 'https://api.payulatam.com/payments-api/4.0/service.cgi'
            }
        return {
            'payulatam_form_url': 'https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu/',
            'payulatam_rest_url': 'https://sandbox.api.payulatam.com/payments-api/4.0/service.cgi'
        }

    def _payulatam_generate_sign(self, inout, values):
        if inout not in ('in', 'in_s2s', 'out'):
            raise Exception("Type must be 'in', 'in_s2s' or 'out'")

        if inout in ['in', 'in_s2s']:
            data_string = ('~').join((self.payulatam_api_key, self.payulatam_merchant_id, values['referenceCode'],
                                      str(values['amount']), values['currency']))
        else:
            data_string = ('~').join((self.payulatam_api_key, self.payulatam_merchant_id, values['referenceCode'],
                                      str(float(values.get('TX_VALUE'))), values['currency'], values.get('transactionState')))
        return md5(data_string.encode('utf-8')).hexdigest()

    @api.multi
    def payulatam_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        tx = self.env['payment.transaction'].search([('reference', '=', values.get('reference'))])
        # payulatam will not allow any payment twise even if payment was failed last time.
        # so, replace reference code if payment is not done or pending.
        if tx.state not in ['done', 'pending']:
            tx.payulatam_reference_code = str(uuid.uuid4())
        payulatam_values = dict(
            values,
            merchantId=self.payulatam_merchant_id,
            accountId=self.payulatam_account_id,
            description=values.get('reference'),
            referenceCode=tx.payulatam_reference_code,
            amount=values['amount'],
            tax='0',  # This is the transaction VAT. If VAT zero is sent the system, 19% will be applied automatically. It can contain two decimals. Eg 19000.00. In the where you do not charge VAT, it should should be set as 0.
            taxReturnBase='0',
            currency=values['currency'].name,
            buyerEmail=values['partner_email'],
            responseUrl=urls.url_join(base_url, '/payment/payulatam/response'),
            extra1=values.get('return_url')
        )
        payulatam_values['signature'] = self._payulatam_generate_sign("in", payulatam_values)
        return payulatam_values

    @api.multi
    def payulatam_get_form_action_url(self):
        self.ensure_one()
        return self._get_payulatam_urls(self.environment)['payulatam_form_url']

    @api.model
    def payulatam_s2s_form_process(self, data):
        payment_token = self.env['payment.token'].sudo().create({
            'cc_number': data['cc_number'],
            'cc_holder_name': data['cc_holder_name'],
            'cc_expiry': data['cc_expiry'],
            'cc_brand': data['cc_brand'],
            'cvc': data['cvc'],
            'acquirer_id': int(data['acquirer_id']),
            'partner_id': int(data['partner_id'])
        })
        return payment_token

    @api.multi
    def payulatam_s2s_form_validate(self, data):
        self.ensure_one()

        # mandatory fields
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand"]:
            if not data.get(field_name):
                return False
        return True


class PaymentTransactionPayulatam(models.Model):
    _inherit = 'payment.transaction'

    # payulatam will not allow any payment twice with same reference even if payment was failed last time
    # so need to change the reference number each time so instead of changing order reference added new field
    payulatam_reference_code = fields.Char('Reference Code', readonly=True)
    # inorder to make refund one extra order ID need to passed which gets from payulatam while transaction.
    payulatam_order_id = fields.Char('Order ID', readonly=True)

    @api.model
    def _payulatam_form_get_tx_from_data(self, data):
        """ Given a data dict coming from payulatam, verify it and find the related
        transaction record. """
        reference, txnid, sign = data.get('referenceCode'), data.get('transactionId'), data.get('signature')
        if not reference or not txnid or not sign:
            raise ValidationError(_('PayUlatam: received data with missing reference (%s) or transaction id (%s) or sign (%s)') % (reference, txnid, sign))

        transaction = self.search([('payulatam_reference_code', '=', reference)])

        if not transaction:
            error_msg = (_('PayUlatam: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('PayUlatam: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)

        # verify shasign
        sign_check = transaction.acquirer_id._payulatam_generate_sign('out', data)
        if sign_check.upper() != sign.upper():
            raise ValidationError(('PayUlatam: invalid sign, received %s, computed %s, for data %s') % (sign, sign_check, data))
        return transaction

    @api.multi
    def _payulatam_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.payulatam_reference_code and data.get('referenceCode') != self.payulatam_reference_code:
            invalid_parameters.append(('Reference code', data.get('referenceCode'), self.payulatam_reference_code))
        if float_compare(float(data.get('TX_VALUE', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('TX_VALUE'), '%.2f' % self.amount))
        if data.get('merchantId') != self.acquirer_id.payulatam_merchant_id:
            invalid_parameters.append(('Merchant Id', data.get('merchantId'), self.acquirer_id.payulatam_merchant_id))
        return invalid_parameters

    @api.multi
    def _create_payulatam_charge(self, **kwargs):
        api_charge_url = self.acquirer_id._get_payulatam_urls(self.acquirer_id.environment)['payulatam_rest_url']
        if self.state not in ['done', 'pending']:
            self.payulatam_reference_code = str(uuid.uuid4())
        charge_data = {
            "language": "en",
            "command": "SUBMIT_TRANSACTION",
            "merchant": {
                "apiKey": self.acquirer_id.payulatam_api_key,
                "apiLogin": self.acquirer_id.payulatam_api_login
            },
            "transaction": {
                "order": {
                    "accountId": self.acquirer_id.payulatam_account_id,
                    "referenceCode": self.payulatam_reference_code,
                    "description": self.reference,
                    "language": "en",
                    "signature": self.acquirer_id._payulatam_generate_sign('in_s2s', {'amount': self.amount, 'referenceCode': self.payulatam_reference_code, 'currency': self.currency_id.name}),
                    "additionalValues": {
                        "TX_VALUE": {  # transaction value
                            "value": self.amount,
                            "currency": self.currency_id.name
                        }
                    }
                },
                "creditCardTokenId": self.payment_token_id.acquirer_ref,
                "creditCard": {
                    "securityCode": kwargs.get('cvc') or kwargs.get('cvc_number')
                },
                "type": "AUTHORIZATION_AND_CAPTURE",
                "paymentMethod": self.payment_token_id.name.split('-')[-1].replace(' ', '').upper()
            },
            'test': 'true' if self.acquirer_id.environment == 'test' else "false"
        }
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(api_charge_url, json.dumps(charge_data), headers=headers)
        data = objectify.fromstring(resp.text)
        _logger.info('_create_payulatam_charge: Values received:\n%s', pprint.pformat(resp.text))
        if data.find('error'):
            raise ValidationError('_create_payulatam_charge: Values received:\n%s' % pprint.pformat(resp.text))
        return data

    @api.multi
    def payulatam_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        result = self._create_payulatam_charge(email=self.partner_email, **kwargs)
        return self._payulatam_form_validate(result)

    def _create_payulatam_refund(self):
        api_refund_url = self.acquirer_id._get_payulatam_urls(self.acquirer_id.environment)['payulatam_rest_url']
        refund_params = {
            "language": "en",
            "command": "SUBMIT_TRANSACTION",
            "merchant": {
                "apiKey": self.acquirer_id.payulatam_api_key,
                "apiLogin": self.acquirer_id.payulatam_api_login
            },
            "transaction": {
                "order": {
                    "id": self.payulatam_order_id
                },
                "type": "REFUND",
                "reason": "Adding card",
                "parentTransactionId": self.acquirer_reference
            },
            "test": 'true' if self.acquirer_id.environment == 'test' else "false"
        }

        headers = {'Content-Type': 'application/json'}
        resp = requests.post(api_refund_url, json.dumps(refund_params), headers=headers)
        data = objectify.fromstring(resp.text)
        _logger.info('_create_payulatam_refund: Values received:\n%s', pprint.pformat(resp.text))
        if data.find('error'):
            raise ValidationError('_create_payulatam_refund: Values received:\n%s' % pprint.pformat(resp.text))
        return data

    @api.multi
    def payulatam_s2s_do_refund(self, **kwargs):
        self.ensure_one()
        result = self._create_payulatam_refund()
        return self._payulatam_form_validate(result)

    @api.multi
    def _payulatam_form_validate(self, data):
        self.ensure_one()

        status = data.get('lapTransactionState') or data.find('transactionResponse').find('state').text
        res = {
            'acquirer_reference': data.get('transactionId') or data.find('transactionResponse').find('transactionId').text,
            'state_message': data.get('message') or ""
        }

        if status == 'APPROVED':
            _logger.info('Validated PayUlatam payment for tx %s: set as done' % (self.reference))
            res.update(state='done', date=fields.Datetime.now())
            if self.payment_token_id:
                res.update(payulatam_order_id=data.find('transactionResponse').find('orderId').text)
                self.payment_token_id.verified = True
            self._set_transaction_done()
            self.write(res)
            self.execute_callback()
            return True
        elif status == 'PENDING':
            _logger.info('Received notification for PayUlatam payment %s: set as pending' % (self.reference))
            res.update(state='pending')
            self._set_transaction_pending()
            return self.write(res)
        elif status in ['EXPIRED', 'DECLINED']:
            _logger.info('Received notification for PayUlatam payment %s: set as Cancel' % (self.reference))
            res.update(state='cancel')
            self._set_transaction_cancel()
            return self.write(res)
        else:
            error = 'Received unrecognized status for PayUlatam payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            res.update(state='cancel', state_message=error)
            self._set_transaction_cancel()
            return self.write(res)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    @api.model
    def payulatam_create(self, values):
        res = {}
        payment_acquirer = self.env['payment.acquirer'].browse(values.get('acquirer_id'))
        if values.get('cc_number'):
            data = json.dumps({
                'language': 'en',
                'command': 'CREATE_TOKEN',
                'merchant': {
                    'apiLogin': payment_acquirer.payulatam_api_login,
                    'apiKey':  payment_acquirer.payulatam_api_key
                },
                'creditCardToken': {
                    'payerId': self.env.user.id,
                    'name': values.get('cc_holder_name'),
                    'paymentMethod': values.get('cc_brand').upper(),
                    'number': values.get('cc_number').replace(' ', ''),
                    'expirationDate': "20" + str(values['cc_expiry'][-2:]) + "/" + str(values['cc_expiry'][:2]),
                },
            })
            headers = {'Content-Type': 'application/json'}
            response = requests.post(payment_acquirer._get_payulatam_urls(payment_acquirer.environment)['payulatam_rest_url'], data, headers=headers)
            data = objectify.fromstring(response.text)
            if data.find('code').text == 'SUCCESS':
                _logger.info('_create_credit_card: Values received:\n%s', pprint.pformat(response.text))
                res = {
                    'acquirer_ref': data.find('creditCardToken').find('creditCardTokenId').text,
                    'name': 'XXXXXXXXXXXX%s - %s - %s' % (values['cc_number'][-4:], values['cc_holder_name'], values['cc_brand'])
                }
            else:
                raise ValidationError(data.find('error').text)
        return res
