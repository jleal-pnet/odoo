# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools

from odoo.addons.test_mail.tests import common as mail_common
from odoo.tests import common
from odoo.tools import mute_logger


class TestUtils(common.SavepointCase, mail_common.MockEmails):

    @classmethod
    def setUpClass(cls):
        super(TestUtils, cls).setUpClass()
        _quick_create_ctx = {
            'no_reset_password': True,
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
        }
        cls.user_employee = cls.env['res.users'].with_context(_quick_create_ctx).create({
            'name': 'Frédéric, le Grand',
            'login': 'fred',
            'email': 'fred@example.com',
            'signature': '--\nFrédéric le Grand',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })
        cls.recipient_1 = cls.env['res.partner'].with_context(_quick_create_ctx).create({
            'name': 'Frédérique, la Petiote',
            'email': 'fred2@example.com',
        })
        cls.recipient_2 = cls.env['res.partner'].with_context(_quick_create_ctx).create({
            'name': 'Amię Wiadomość',
            'email': 'amy@example.com',
        })

    def test_build_email_from_mail(self):
        # print('--------------------------------------------------')
        mail = self.env['mail.mail'].sudo(self.user_employee).create({
            'subject': 'Żółta kartka',
            'body': '<p>Zizisse top body</p>',
            'recipient_ids': [(4, self.recipient_1.id), (4, self.recipient_2.id)],
            'email_to': ', '.join(['Alexandra, Méga Défonçeuse <alexandra@example.com>', 'Amię Wiadomość <amy@example.com>']),
            # 'email_cc':', '.join(['Alexandra, Méga Défonçeuse <alexandra@example.com>', 'Amię Wiadomość <amy@example.com>']),
        })
        # print('--------------------------------------------------')
        mail.send()
        # print('--------------------------------------------------')


class TestMail(common.SavepointCase, mail_common.MockEmails):

    @classmethod
    def setUpClass(cls):
        super(TestMail, cls).setUpClass()

        cls.user_employee = cls.env['res.users'].with_context({
            'no_reset_password': True,
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
        }).create({
            'name': 'Ernest Employee',
            'login': 'ernest',
            'email': 'e.e@example.com',
            'signature': '--\nErnest',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_mail_message_notify_from_mail_mail(self):
        # Due ot post-commit hooks, store send emails in every step
        self.email_to_list = []
        mail = self.env['mail.mail'].create({
            'body_html': '<p>Test</p>',
            'email_to': 'test@example.com',
            'partner_ids': [(4, self.user_employee.partner_id.id)]
        })
        self.email_to_list.extend(itertools.chain.from_iterable(sent_email['email_to'] for sent_email in self._mails if sent_email.get('email_to')))
        self.assertNotIn(u'Ernest Employee <e.e@example.com>', self.email_to_list)
        mail.send()
        self.email_to_list.extend(itertools.chain.from_iterable(sent_email['email_to'] for sent_email in self._mails if sent_email.get('email_to')))
        self.assertNotIn(u'Ernest Employee <e.e@example.com>', self.email_to_list)
        self.assertIn(u'test@example.com', self.email_to_list)
