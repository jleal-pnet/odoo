# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_uri(self):
        return "%s/auth_oauth/signin" % (self.env['ir.config_parameter'].get_param('web.base.url'))

    auth_oauth_google_enabled = fields.Boolean(string='Allow users to sign in with Google')
    auth_oauth_google_client_id = fields.Char(string='Client ID')
    server_uri_google = fields.Char(string='Server uri')
    auth_oauth_azure_enabled = fields.Boolean(string='Allow users to sign in with Azure')
    auth_oauth_azure_client_id = fields.Char(string='Azure Client ID')
    auth_oauth_azure_client_password = fields.Char(string='Azure Client Password')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        google_provider = self.env.ref('auth_oauth.provider_google', False)
        azure_provider = self.env.ref('auth_oauth.provider_azure', False)
        res.update(
            auth_oauth_google_enabled=google_provider.enabled,
            auth_oauth_google_client_id=google_provider.client_id,
            server_uri_google=self.get_uri(),
            auth_oauth_azure_enabled=azure_provider.enabled,
            auth_oauth_azure_client_id=azure_provider.client_id,
            auth_oauth_azure_client_password=azure_provider.client_secret,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        google_provider = self.env.ref('auth_oauth.provider_google', False)
        azure_provider = self.env.ref('auth_oauth.provider_azure', False)
        google_provider.write({
            'enabled': self.auth_oauth_google_enabled,
            'client_id': self.auth_oauth_google_client_id,
        })
        azure_provider.write({
            'enabled': self.auth_oauth_azure_enabled,
            'client_id': self.auth_oauth_azure_client_id,
            'client_secret': self.auth_oauth_azure_client_password,
        })
