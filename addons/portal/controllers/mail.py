# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import werkzeug
from werkzeug.exceptions import NotFound, Forbidden

from odoo import http, tools
from odoo.http import request
from odoo.osv import expression
from odoo.tools import consteq, plaintext2html
from odoo.addons.web.controllers.main import binary_content
from odoo.modules import get_module_resource


def _has_token_access(res_model, res_id, token=''):
    record = request.env[res_model].browse(res_id).sudo()
    token_field = request.env[res_model]._mail_post_token_field
    return (token and record and consteq(record[token_field], token))

def _message_post_helper(res_model='', res_id=None, message='', token='', nosubscribe=True, **kw):
    """ Generic chatter function, allowing to write on *any* object that inherits mail.thread.
        If a token is specified, all logged in users will be able to write a message regardless
        of access rights; if the user is the public user, the message will be posted under the name
        of the partner_id of the object (or the public user if there is no partner_id on the object).

        :param string res_model: model name of the object
        :param int res_id: id of the object
        :param string message: content of the message

        optional keywords arguments:
        :param string token: access token if the object's model uses some kind of public access
                             using tokens (usually a uuid4) to bypass access rules
        :param bool nosubscribe: set False if you want the partner to be set as follower of the object when posting (default to True)

        The rest of the kwargs are passed on to message_post()
    """
    record = request.env[res_model].browse(res_id)
    author_id = request.env.user.partner_id.id if request.env.user.partner_id else False
    if token:
        access_as_sudo = _has_token_access(res_model, res_id, token=token)
        if access_as_sudo:
            record = record.sudo()
            if request.env.user == request.env.ref('base.public_user'):
                author_id = record.partner_id.id if hasattr(record, 'partner_id') else author_id
            else:
                if not author_id:
                    raise NotFound()
        else:
            raise Forbidden()
    kw.pop('csrf_token', None)
    kw.pop('attachment_ids', None)
    return record.with_context(mail_create_nosubscribe=nosubscribe).message_post(body=message,
                                                                                   message_type=kw.pop('message_type', "comment"),
                                                                                   subtype=kw.pop('subtype', "mt_comment"),
                                                                                   author_id=author_id,
                                                                                   **kw)


class PortalChatter(http.Controller):

    @http.route(['/mail/chatter_post'], type='json', methods=['POST'], auth='public', website=True)
    def portal_chatter_post(self, res_model, res_id, message, **kw):
        url = request.httprequest.referrer
        if message:
            # message is received in plaintext and saved in html
            message = plaintext2html(message)
            _message_post_helper(res_model, int(res_id), message, **kw)
            url = url + "#discussion"
        return url

    @http.route('/mail/chatter_init', type='json', auth='public', website=True)
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        is_user_public = request.env.user.has_group('base.group_public')
        message_data = self.portal_message_fetch(res_model, res_id, domain=domain, limit=limit, **kwargs)
        display_composer = False
        if kwargs.get('allow_composer'):
            display_composer = kwargs.get('token') or not is_user_public
        return {
            'messages': message_data['messages'],
            'options': {
                'message_count': message_data['message_count'],
                'is_user_public': is_user_public,
                'is_user_publisher': request.env.user.has_group('website.group_website_publisher'),
                'display_composer': display_composer,
                'partner_id': request.env.user.partner_id.id
            }
        }

    @http.route('/mail/chatter_fetch', type='json', auth='public', website=True)
    def portal_message_fetch(self, res_model, res_id, domain=False, limit=10, offset=0, **kw):
        if not domain:
            domain = []
        # Only search into website_message_ids, so apply the same domain to perform only one search
        # extract domain from the 'website_message_ids' field
        field_domain = request.env[res_model]._fields['website_message_ids'].domain
        domain += field_domain(request.env[res_model]) if callable(field_domain) else field_domain
        domain += [('res_id', '=', res_id)]
        # Check access
        Message = request.env['mail.message']
        if kw.get('token'):
            access_as_sudo = _has_token_access(res_model, res_id, token=kw.get('token'))
            if not access_as_sudo:  # if token is not correct, raise Forbidden
                raise Forbidden()
            # Non-employee see only messages with not internal subtype (aka, no internal logs)
            if not request.env['res.users'].has_group('base.group_user'):
                domain = expression.AND([['&', ('subtype_id', '!=', False), ('subtype_id.internal', '=', False)], domain])
            Message = request.env['mail.message'].sudo()
        return {
            'messages': Message.search(domain, limit=limit, offset=offset).portal_message_format(),
            'message_count': Message.search_count(domain)
        }

    @http.route([
        '/portal/image/<string:res_model>/<int:partner_id>/<string:field_name>',
        '/portal/image/<string:res_model>/<int:partner_id>/<string:field_name>/<int:width>x<int:height>'
        ], type='http', auth='public')
    def avatar(self, res_model, partner_id, field_name, width=50, height=50):
        status, headers, content = binary_content(model=res_model, id=partner_id, field=field_name)
        if status == 304:
            return werkzeug.wrappers.Response(status=304)

        if not content:
            img_path = get_module_resource('base', 'static/img', 'avatar.png')
            content = tools.image_resize_image(base64.b64encode(open(img_path, 'rb').read()), (width, height))
            headers = [('Content-Type', 'image/png')]

        image_base64 = base64.b64decode(content)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response

    @http.route('/portal/content/<int:attachment_id>', type='http', auth="public")
    def attachment_access(self, attachment_id, access_token=None, download=None):
        status, headers, content = binary_content(id=attachment_id, download=download, access_token=access_token)
        if status == 304:
            return werkzeug.wrappers.Response(status=304)

        attachment_sudo = request.env['ir.attachment'].sudo().browse(attachment_id).exists()
        if access_token and consteq(attachment_sudo.access_token, access_token):
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            return request.make_response(content_base64, headers)
        else:
            raise Forbidden()
