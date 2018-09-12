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
    additional_info = fields.Char('Additional info')

    IAP_URL = 'https://partner-autocomplete.odoo.com/iap/partner_autocomplete'
    IAP_URL = 'https://odoo-iap-apps-master-partner-autocomplete-service-twa-128360.dev.odoo.com/iap/partner_autocomplete'
    IAP_URL = 'http://odoo:8069/iap/partner_autocomplete'

    @api.model
    def _format_data_company_contact(self, contacts):
        formatted = []
        for contact in contacts:
            country_data = self._find_country_data(
                state_code=contact.get('state_code', False),
                state_name=contact.get('state_name', False),
                country_code=contact.get('country_code', False),
                country_name=contact.get('country_name', False)
            )
            formatted.append({
                'type': contact.get('type'),
                'name': contact.get('name'),
                'country_id': country_data.get('country_id'),
                'state_id': country_data.get('state_id'),
                'street': '%s %s' % (contact.get('street_name'), contact.get('street_number')),
                'city': contact.get('city', ''),
                'zip': contact.get('postal_code', ''),
                'phone': contact.get('phone', ''),
                'email': contact.get('email', ''),
            })
        return formatted

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

        phone = company_data.get('phone', '')
        if not phone and len(phones) > 0:
            phone = phones.pop(0)

        email = False
        if len(emails) > 0:
            email = emails.pop(0)

        paragraphs = []
        lines = []

        lines.append({
            'title': _('Description'),
            'content': company_data.get('description', ''),
            'new_line': True
        })

        paragraphs.append(lines)
        lines = []

        if company_data.get('employees'):
            lines.append({
                'title': _('Employees'),
                'content': lang.format('%.0f', float(company_data.get('employees')), True, True),
            })
        if company_data.get('annual_revenue'):
            lines.append({
                'title': _('Annual revenue'),
                'content': '$%s' % lang.format('%.0f', float(company_data.get('annual_revenue')), True, True),
            })
        if company_data.get('estimated_annual_revenue'):
            lines.append({
                'title': _('Estimated annual revenue'),
                'content': company_data.get('estimated_annual_revenue'),
            })
        if company_data.get('sector'):
            lines.append({
                'title': _('Sector'),
                'content': company_data.get('sector'),
            })
        if company_data.get('tech'):
            lines.append({
                'title': _('Tech'),
                'content': ' / '.join(company_data.get('tech', [])),
            })

        if lines:
            paragraphs.append(lines)
            lines = []

        social_medias = 'facebook,linkedin,crunchbase,twitter'.split(',')
        for social_media in social_medias:
            if company_data.get(social_media):
                lines.append({
                    'content': "&nbsp;&nbsp;&nbsp; www.%s.com/%s" % (social_media, company_data.get(social_media)),
                })

        if lines:
            lines.insert(0, {
                'title': _('Social networks'),
            })
            paragraphs.append(lines)
            lines = []

        if emails:
            lines.append({
                'title': _('Email addresses'),
            })
            for email in emails:
                lines.append({
                    'content': '&nbsp;&nbsp;&nbsp; <a href="mailto:%s">%s</a>' % (email, email),
                })
            paragraphs.append(lines)
            lines = []

        if phones:
            lines.append({
                'title': _('Phone numbers'),
            })
            for phone in phones:
                lines.append({
                    'content': '&nbsp;&nbsp;&nbsp; %s' % phone,
                })

        additional_info = ""
        for paragraph in paragraphs:
            additional_info += '<p>'
            for line in paragraph:
                if line.get('title', ''):
                    additional_info += "<b>%s</b>" % line.get('title', '')
                    additional_info += '<br>' if line.get('new_line') else ' : '
                additional_info += line.get('content', '')
                additional_info += '<br>'
            additional_info += '</p>'

        company = {
            'country_id': country_data.get('country_id'),
            'state_id': country_data.get('state_id'),
            'website': company_data.get('domain', ''),
            'name': company_data.get('name', ''),
            'additional_info': additional_info,
            'street': '%s %s' % (company_data.get('street_name', ''), company_data.get('street_number', '')),
            'city': company_data.get('city', ''),
            'zip': company_data.get('postal_code', ''),
            'phone': phone,
            'email': email,
            'company_data_id': company_data.get('company_data_id'),
            'vat': company_data.get('vat', ''),
            'logo': company_data.get('logo', ''),
            'bank_ids': company_data.get('bank_accounts') if company_data.get('bank_accounts') else [],
            'child_ids': self._format_data_company_contact(company_data.get('contacts')) if company_data.get('contacts') else [],
        }

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
    def _rpc_remote_api(self, action, params, timeout=15):
        url = '%s/%s' % (self.IAP_URL, action)
        params.update({
            'db_uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
            'country_code': self.env.user.company_id.country_id.code,
            'zip': self.env.user.company_id.zip,
        })
        try:
            return jsonrpc(url=url, params=params, timeout=timeout), False
        except (ConnectionError, HTTPError, exceptions.AccessError) as exception:
            _logger.error('Autocomplete API error: %s' % str(exception))
            return False, str(exception)

    @api.model
    def autocomplete(self, query):
        def format_results(suggestions):
            results = []
            for suggestion in suggestions:
                # If coming from our IAP DB, should be reformatted
                # ex: company.domain -> company.website
                #     concat comments
                #     etc...
                if suggestion.get('company_data_id') or suggestion.get('vat'):
                    results.append(self._format_data_company(suggestion))
                else:
                    results.append(suggestion)
            return results

        suggestions, error = self._rpc_remote_api('search', {
            'query': query,
        })
        if suggestions:
            return format_results(suggestions)
        else:
            return []

    @api.model
    def enrich_company(self, company_domain, company_data_id):
        enrichment_data, error = self._rpc_remote_api('enrich', {
            'domain': company_domain,
            'company_data_id': company_data_id,
        })
        if enrichment_data:
            return self._format_data_company(enrichment_data)
        else:
            return {}

    @api.model
    def read_by_vat(self, vat):
        vies_vat_data, error = self._rpc_remote_api('search_vat', {
            'vat': vat,
        })
        if vies_vat_data:
            return [self._format_data_company(vies_vat_data)]
        else:
            return []

    @api.model
    def _is_company_in_europe(self, country_code):
        country = self.env['res.country'].search([('code', '=ilike', country_code)])
        if country:
            country_id = country.id
            europe = self.env.ref('base.europe')
            if not europe:
                europe = self.env["res.country.group"].search([('name', '=', 'Europe')], limit=1)
            if not europe or country_id not in europe.country_ids.ids:
                return False
        return True

    def _is_vat_syncable(self, vat):
        vat_country_code = vat[:2]
        partner_country_code = self.country_id and self.country_id.code
        return self._is_company_in_europe(vat_country_code) and (partner_country_code == vat_country_code or not partner_country_code)

    def _update_autocomplete_data(self, vat):
        self.ensure_one()
        if vat and self.is_company and self.company_data_id and self._is_vat_syncable(vat):
            self.env['res.partner.autocomplete.sync'].sudo().add_to_queue(self.id)

    @api.model
    def create(self, values):
        record = super(ResPartner, self).create(values)
        record._update_autocomplete_data(values.get('vat', False))

        if record.additional_info:
            record.message_post(body=record.additional_info)
            record.write({'additional_info': False})

        return record

    @api.multi
    def write(self, values):
        record = super(ResPartner, self).write(values)
        for partner in self:
            partner._update_autocomplete_data(values.get('vat', False))

        return record
