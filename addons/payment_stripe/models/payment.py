# coding: utf-8

import json
import logging
import requests
import pprint

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

# Force the API version to avoid breaking in case of update on Stripe side
# cf https://stripe.com/docs/api#versioning
# changelog https://stripe.com/docs/upgrades#api-changelog
STRIPE_HEADERS = {'Stripe-Version': '2016-03-07'}

# The following currencies are integer only, see https://stripe.com/docs/currencies#zero-decimal
INT_CURRENCIES = [
    u'BIF', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
]


class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('stripe', 'Stripe')])
    stripe_secret_key = fields.Char(required_if_provider='stripe', groups='base.group_user')
    stripe_publishable_key = fields.Char(required_if_provider='stripe', groups='base.group_user')
    stripe_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user',
        help="A relative or absolute URL pointing to a square image of your "
             "brand or product. As defined in your Stripe profile. See: "
             "https://stripe.com/docs/checkout")
    payment_method_ids = fields.Many2many('stripe.payment.method', string="Payment Method")

    @api.multi
    def stripe_form_generate_values(self, tx_values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        stripe_tx_values = dict(tx_values)
        temp_stripe_tx_values = {
            'amount': tx_values['amount'],  # Mandatory
            'currency': tx_values['currency'].name,  # Mandatory anyway
            'email': tx_values.get('partner_email'),
            'city': tx_values.get('partner_city'),
            'country': tx_values.get('partner_country').code,
            'name': tx_values.get('partner_name'),
            'reference': tx_values.get('reference'),
            'return_url': tx_values.get('return_url'),
            'redirect_url': urls.url_join(base_url, '/payment/stripe/return?acquirer_id=' + str(self.id)),
            'city': tx_values.get('partner_city'),
            'line1': tx_values.get('partner_address'),
            'postal_code': tx_values.get('partner_zip'),
            'state': tx_values.get('partner_state').code
        }
        temp_stripe_tx_values['returndata'] = stripe_tx_values.pop('return_url', '')
        stripe_tx_values.update(temp_stripe_tx_values)
        return stripe_tx_values

    @api.model
    def _get_stripe_api_url(self):
        return 'https://api.stripe.com/v1'

    @api.model
    def stripe_s2s_form_process(self, data):
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
    def stripe_s2s_form_validate(self, data):
        self.ensure_one()

        # mandatory fields
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand"]:
            if not data.get(field_name):
                return False
        return True

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerStripe, self)._get_feature_support()
        res['tokenize'].append('stripe')
        return res

    def get_stripe_url(self):
        return self._get_stripe_api_url()


class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'

    stripe_payment_type = fields.Char(string='Stripe Payment Type', groups='base.group_user')

    def get_stripe_resp(self, data, req_type):
        headers = {'AUTHORIZATION': 'Bearer %s' % self.acquirer_id.stripe_secret_key}
        url = "%s/%s" % (self.acquirer_id.get_stripe_url(), req_type)
        resp = requests.post(url, data=data, headers=headers)
        return json.loads(resp.text)

    def _do_generic_stripe_payment(self, **kwargs):
        self = self.search([('reference', '=', kwargs.get('metadata', {}).get('reference'))])
        charge_data = {
            'amount': kwargs.get('amount'),
            'currency': kwargs.get('currency'),
            'source': kwargs.get('id'),
        }
        charge_resp = self.get_stripe_resp(charge_data, 'charges')
        _logger.info('Stripe: take charge %s %s' % (charge_resp.get('source', {}).get('type'), pprint.pformat(charge_resp.get('source'))))
        return charge_resp.get('source')

    def get_stripe_source_data(self, **kwargs):
        return {
            "type": kwargs.get('type'),
            'amount': kwargs.get('amount'),
            'currency': kwargs.get('currency'),
            'metadata[return_url]': kwargs.get('metadata[return_url]'),
            'metadata[reference]':  kwargs.get('metadata[reference]'),
            'owner[name]': kwargs.get('owner[name]'),
            'owner[address][city]': kwargs.get('owner[address][city]'),
            'owner[address][line1]': kwargs.get('owner[address][line1]'),
            'owner[address][state]': kwargs.get('owner[address][state]'),
            'owner[address][country]': kwargs.get('owner[address][country]'),
            'owner[address][postal_code]': kwargs.get('owner[address][postal_code]'),
        }

    def _do_card_stripe_payment(self, **kwargs):
        source_data = self.get_stripe_source_data(**kwargs)
        source_data.update({
            'card[number]': kwargs.get('card[number]'),
            'card[exp_month]': kwargs.get('card[exp_month]'),
            'card[exp_year]': kwargs.get('card[exp_year]'),
            'card[cvc]': kwargs.get('card[cvc]'),
        })
        source_resp = self.get_stripe_resp(source_data, 'sources')
        if not source_resp.get('id'):
            raise ValidationError(_('Stripe: cannot create token card %s' % pprint.pformat(source_resp)))
        _logger.info('Stripe: create token card %s' % pprint.pformat(source_resp))
        charge_data = {
            'amount': kwargs.get('amount'),
            'currency': kwargs.get('currency'),
            'source': source_resp.get('id'),
        }
        charge_resp = self.get_stripe_resp(charge_data, 'charges')
        if not charge_resp.get('id'):
            raise ValidationError(_('Stripe: cannot take charge card %s' % pprint.pformat(charge_resp)))
        _logger.info('Stripe: take charge card  %s' % pprint.pformat(charge_resp))
        self.form_feedback(charge_resp.get('source'), 'stripe')
        return_url = charge_resp.get('source').get('metadata', {}).get('return_url') or "/"
        return return_url

    def _do_sepa_debit_stripe_payment(self, **kwargs):
        source_data = self.get_stripe_source_data(**kwargs)
        source_data.update({
            "sepa_debit[iban]": kwargs.get('sepa_debit[iban]'),
        })
        source_resp = self.get_stripe_resp(source_data, 'sources')
        if not source_resp.get('id'):
            raise ValidationError(_('Stripe: cannot create source sepa debit %s' % pprint.pformat(source_resp)))
        _logger.info('Stripe: create source sepa debit %s' % pprint.pformat(source_resp))
        cust_data = {
            'email': self.env.user.partner_id.email,
            'source': source_resp.get('id')
        }
        cust_resp = self.get_stripe_resp(cust_data, 'customers')
        if not cust_resp.get('id'):
            raise ValidationError(_('Stripe: cannot create customer sepa debit %s' % pprint.pformat(cust_resp)))
        _logger.info('Stripe: create customer sepa debit %s' % pprint.pformat(cust_resp))
        charge_data = {
            'amount': kwargs.get('amount'),
            'currency': kwargs.get('currency'),
            'source': source_resp.get('id'),
            'customer': cust_resp.get('id')
        }
        response_data = self.get_stripe_resp(charge_data, 'charges')
        if not response_data.get('id'):
            raise ValidationError(_('Stripe: cannot take charge sepa debit %s' % pprint.pformat(response_data)))
        _logger.info('Stripe: take charge sepa debit %s' % pprint.pformat(response_data))
        self.form_feedback(response_data.get('source'), 'stripe')
        return_url = response_data.get('source').get('metadata', {}).get('return_url') or "/"
        return return_url

    def do_stripe_payment(self, **kwargs):
        if kwargs.get('type') == 'card':
            return self._do_card_stripe_payment(**kwargs)
        elif kwargs.get('type') == 'sepa_debit':
            return self._do_sepa_debit_stripe_payment(**kwargs)
        else:
            return self._do_generic_stripe_payment(**kwargs)

    def _create_stripe_charge(self, acquirer_ref=None, tokenid=None, email=None):
        api_url_charge = '%s/charges' % (self.acquirer_id._get_stripe_api_url())
        charge_params = {
            'amount': int(self.amount if self.currency_id.name in INT_CURRENCIES else float_round(self.amount * 100, 2)),
            'currency': self.currency_id.name,
            'metadata[reference]': self.reference,
            'description': self.reference,
        }
        if acquirer_ref:
            charge_params['customer'] = acquirer_ref
        if tokenid:
            charge_params['card'] = str(tokenid)
        if email:
            charge_params['receipt_email'] = email.strip()

        _logger.info('_create_stripe_charge: Sending values to URL %s, values:\n%s', api_url_charge, pprint.pformat(charge_params))
        r = requests.post(api_url_charge,
                          auth=(self.acquirer_id.stripe_secret_key, ''),
                          params=charge_params,
                          headers=STRIPE_HEADERS)
        res = r.json()
        _logger.info('_create_stripe_charge: Values received:\n%s', pprint.pformat(res))
        return res

    @api.multi
    def stripe_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        result = self._create_stripe_charge(acquirer_ref=self.payment_token_id.acquirer_ref, email=self.partner_email)
        return self._stripe_s2s_validate_tree(result)


    def _create_stripe_refund(self):
        api_url_refund = '%s/refunds' % (self.acquirer_id._get_stripe_api_url())

        refund_params = {
            'charge': self.acquirer_reference,
            'amount': int(float_round(self.amount * 100, 2)), # by default, stripe refund the full amount (we don't really need to specify the value)
            'metadata[reference]': self.reference,
        }

        _logger.info('_create_stripe_refund: Sending values to URL %s, values:\n%s', api_url_refund, pprint.pformat(refund_params))
        r = requests.post(api_url_refund,
                            auth=(self.acquirer_id.stripe_secret_key, ''),
                            params=refund_params,
                            headers=STRIPE_HEADERS)
        res = r.json()
        _logger.info('_create_stripe_refund: Values received:\n%s', pprint.pformat(res))
        return res

    @api.multi
    def stripe_s2s_do_refund(self, **kwargs):
        self.ensure_one()
        result = self._create_stripe_refund()
        return self._stripe_s2s_validate_tree(result)

    @api.model
    def _stripe_form_get_tx_from_data(self, data):
        """ Given a data dict coming from stripe, verify it and find the related
        transaction record. """
        reference = data.get('metadata', {}).get('reference')
        if not reference:
            stripe_error = data.get('error', {}).get('message', '')
            _logger.error('Stripe: invalid reply received from stripe API, looks like '
                          'the transaction failed. (error: %s)', stripe_error  or 'n/a')
            error_msg = _("We're sorry to report that the transaction has failed.")
            if stripe_error:
                error_msg += " " + (_("Stripe gave us the following info about the problem: '%s'") %
                                    stripe_error)
            error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
                                 "credit card details, or contacting your bank?")
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx:
            error_msg = (_('Stripe: no order found for reference %s') % reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = (_('Stripe: %s orders found for reference %s') % (len(tx), reference))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    @api.multi
    def _stripe_s2s_validate_tree(self, tree):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info('Stripe: trying to validate an already validated tx (ref %s)', self.reference)
            return True
        status = tree.get('status')
        if status in ['succeeded', 'consumed']:
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': tree.get('id'),
                'stripe_payment_type': tree.get('type')
            })
            self._set_transaction_done()
            self.execute_callback()
            if self.payment_token_id:
                self.payment_token_id.verified = True
            return True
        elif status in ['pending', 'chargeable']:
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': tree.get('id'),
                'stripe_payment_type': tree.get('type')
            })
            self._set_transaction_pending()
        else:
            error = tree.get('error', {}).get('message')
            _logger.warn(error)
            self.sudo().write({
                'state_message': error,
                'acquirer_reference': tree.get('id'),
                'date': fields.datetime.now(),
                'stripe_payment_type': tree.get('type')
            })
            self._set_transaction_cancel()
            return False

    @api.multi
    def _stripe_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        reference = data['metadata']['reference']
        if reference != self.reference:
            invalid_parameters.append(('Reference', reference, self.reference))
        return invalid_parameters

    @api.multi
    def _stripe_form_validate(self,  data):
        return self._stripe_s2s_validate_tree(data)


class PaymentTokenStripe(models.Model):
    _inherit = 'payment.token'

    @api.model
    def stripe_create(self, values):
        token = values.get('stripe_token')
        description = None
        payment_acquirer = self.env['payment.acquirer'].browse(values.get('acquirer_id'))
        # when asking to create a token on Stripe servers
        if values.get('cc_number'):
            url_token = '%s/tokens' % payment_acquirer._get_stripe_api_url()
            payment_params = {
                'card[number]': values['cc_number'].replace(' ', ''),
                'card[exp_month]': str(values['cc_expiry'][:2]),
                'card[exp_year]': str(values['cc_expiry'][-2:]),
                'card[cvc]': values['cvc'],
                'card[name]': values['cc_holder_name'],
            }
            r = requests.post(url_token,
                              auth=(payment_acquirer.stripe_secret_key, ''),
                              params=payment_params,
                              headers=STRIPE_HEADERS)
            token = r.json()
            description = values['cc_holder_name']
        else:
            partner_id = self.env['res.partner'].browse(values['partner_id'])
            description = 'Partner: %s (id: %s)' % (partner_id.name, partner_id.id)

        if not token:
            raise Exception('stripe_create: No token provided!')

        res = self._stripe_create_customer(token, description, payment_acquirer.id)

        # pop credit card info to info sent to create
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand", "stripe_token"]:
            values.pop(field_name, None)
        return res


    def _stripe_create_customer(self, token, description=None, acquirer_id=None):
        if token.get('error'):
            _logger.error('payment.token.stripe_create_customer: Token error:\n%s', pprint.pformat(token['error']))
            raise Exception(token['error']['message'])

        if token['object'] != 'token':
            _logger.error('payment.token.stripe_create_customer: Cannot create a customer for object type "%s"', token.get('object'))
            raise Exception('We are unable to process your credit card information.')

        if token['type'] != 'card':
            _logger.error('payment.token.stripe_create_customer: Cannot create a customer for token type "%s"', token.get('type'))
            raise Exception('We are unable to process your credit card information.')

        payment_acquirer = self.env['payment.acquirer'].browse(acquirer_id or self.acquirer_id.id)
        url_customer = '%s/customers' % payment_acquirer._get_stripe_api_url()

        customer_params = {
            'source': token['id'],
            'description': description or token["card"]["name"]
        }

        r = requests.post(url_customer,
                        auth=(payment_acquirer.stripe_secret_key, ''),
                        params=customer_params,
                        headers=STRIPE_HEADERS)
        customer = r.json()

        if customer.get('error'):
            _logger.error('payment.token.stripe_create_customer: Customer error:\n%s', pprint.pformat(customer['error']))
            raise Exception(customer['error']['message'])

        values = {
            'acquirer_ref': customer['id'],
            'name': 'XXXXXXXXXXXX%s - %s' % (token['card']['last4'], customer_params["description"])
        }

        return values


class PaymentMethodStripe(models.Model):
    _name = 'stripe.payment.method'

    name = fields.Char(string="Payment Name")
    country_ids = fields.Many2many('res.country', string="Country")
