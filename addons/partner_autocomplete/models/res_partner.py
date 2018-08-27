# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models, exceptions, _
from odoo.addons.iap import jsonrpc
from requests.exceptions import ConnectionError, HTTPError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    company_data_id = fields.Integer('Company database ID')

    IAP_URL = 'https://partner-autocomplete.odoo.com/iap/partner_autocomplete'

    @api.model
    def _format_data_company(self, company_data):
        lang_code = self._context.get('lang') or 'en_US'
        lang = self.env['res.lang']._lang_get(lang_code)

        country_data = self._find_country_data(
            state_code=company_data.get('state_code', False),
            state_name=company_data.get('state_name', False),
            country_code=company_data.get('country_code', False),
            country_name=company_data.get('country_name', False)
        )

        phones = company_data.get('phone_numbers', [])
        emails = company_data.get('email', [])

        phone = company_data.get('phone')
        if not phone and len(phones) > 0:
            phone = phones.pop(0)

        email = False
        if len(emails) > 0:
            email = emails.pop(0)

        comment = []
        comment.append("Description: \n%s" % company_data.get('description'))
        comment.append("")

        subcomments = []
        if company_data.get('employees'):
            subcomments.append("Employees : %s" % lang.format('%.0f', float(company_data.get('employees')), True, True))
        if company_data.get('annual_revenue'):
            subcomments.append("Annual revenue : %s" % '$%s' % lang.format('%.0f', float(company_data.get('annual_revenue')), True, True))
        if company_data.get('estimated_annual_revenue'):
            subcomments.append("Estimated annual revenue : %s" % company_data.get('estimated_annual_revenue'))
        if company_data.get('sector'):
            subcomments.append("Sector : %s" % company_data.get('sector'))
        if company_data.get('tech'):
            subcomments.append("Tech : %s" % ' / '.join(company_data.get('tech', [])))

        if subcomments:
            comment += subcomments
            comment.append("")
            subcomments = []

        if company_data.get('facebook'):
            subcomments.append("    www.facebook.com/%s" % company_data.get('facebook'))
        if company_data.get('linkedin'):
            subcomments.append("    www.linkedin.com/%s" % company_data.get('linkedin'))
        if company_data.get('crunchbase'):
            subcomments.append("    www.crunchbase.com/%s" % company_data.get('crunchbase'))
        if company_data.get('twitter'):
            subcomments.append("    www.twitter.com/%s" % company_data.get('twitter'))

        if subcomments:
            comment.append("Social networks :")
            comment += subcomments
            comment.append("")

        if emails:
            comment.append("Email addresses :\n    %s" % '\n    '.join(emails))
            comment.append("")
        if phones:
            comment.append("Phone numbers :\n    %s" % '\n    '.join(phones))

        comment = "\n".join(comment)

        company = {
            'country_id': country_data.get('country_id'),
            'state_id': country_data.get('state_id'),
            'website': company_data.get('domain'),
            'name': company_data.get('name'),
            'comment': comment,
            'city': company_data.get('city'),
            'zip': company_data.get('postal_code'),
            'phone': phone,
            'email': email,
            'company_data_id': company_data.get('company_data_id'),
            'vat': company_data.get('vat'),
            'logo': company_data.get('logo'),
        }
        street = self._split_street_with_params('%s %s' % (company_data.get('street_name'), company_data.get('street_number')), '%(street_name)s, %(street_number)s/%(street_number2)s')
        company.update(street)

        return company


    @api.model
    def _find_country_data(self, state_code, state_name, country_code, country_name):
        result = {
            'country_id': False,
            'state_id': False
        }

        country_id = self.env['res.country'].search([['code', '=ilike', country_code]])
        if not country_id:
            country_id = self.env['res.country'].search([['name', '=ilike', country_name]])

        if country_id:
            result['country_id'] = {
                'id': country_id.id,
                'display_name': country_id.display_name
            }
            if state_name or state_code:
                state_id = self.env['res.country.state'].search([
                    ('country_id', '=', country_id.id),
                    '|',
                        ('name', '=ilike', state_name),
                        ('code', '=ilike', state_code)
                    ], limit=1)

                if state_id:
                    result['state_id'] = {
                        'id': state_id.id,
                        'display_name': state_id.display_name
                    }

        else:
            _logger.info('Country code not found: %s', country_code)

        return result

    @api.model
    def autocomplete(self, query):
        def format_results(suggestions):
            results = []
            for suggestion in suggestions:
                # If coming from our IAP DB, should be reformatted
                # ex: company.domain -> company.website
                #     concat comments
                #     etc...
                if suggestion.get('company_data_id'):
                    results.append(self._format_data_company(suggestion))
                else:
                    results.append(suggestion)
            return results

        suggestions = False

        try:
            url = '%s/search' % self.IAP_URL
            params = {
                'query': query,
                'country_code': self.env.user.company_id.country_id.code,
            }

            suggestions = jsonrpc(url, params=params)
            suggestions = format_results(suggestions)
        except (ConnectionError, HTTPError, exceptions.AccessError ) as exception:
            _logger.error('Autocomplete API error: %s' % str(exception))
            raise exceptions.UserError(_('Connection to Autocomplete API failed.'))

        return suggestions

    @api.model
    def enrich_company(self, company_domain, company_data_id):
        enrichment_data = False

        try:
            url = '%s/enrich' % self.IAP_URL
            params = {
                'domain': company_domain,
                'company_data_id': company_data_id,
                'country_code': self.env.user.company_id.country_id.code,
            }
            enrichment_data = jsonrpc(url, params=params)
            if enrichment_data:
                enrichment_data = self._format_data_company(enrichment_data)
        except (ConnectionError, HTTPError, exceptions.AccessError ) as exception:
            _logger.error('Enrichment API error: %s' % str(exception))
            raise exceptions.UserError(_('Connection to Encrichment API failed.'))

        return enrichment_data

    @api.model
    def read_by_vat(self, vat):
        vies_vat_data = False

        try:
            url = '%s/search_vat' % self.IAP_URL
            params = {
                'vat': vat,
                'country_code': self.env.user.company_id.country_id.code,
            }

            vies_vat_data = jsonrpc(url, params=params)
            if vies_vat_data:
                vies_vat_data = self._format_data_company(vies_vat_data)
        except (ConnectionError, HTTPError, exceptions.AccessError) as exception:
            _logger.error('Enrichment API error: %s' % str(exception))
            raise exceptions.UserError(_('Connection to Encrichment API failed.'))

        return vies_vat_data
