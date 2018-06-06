# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase

class TestWritedateOnNoStoreField(TransactionCase):

    """ Tests that write_date is updated when write on image field.
    """
    def test_write_date_update(self):
        User = self.env['res.users'].browse(self.env.uid)

        write_date_before = User.write_date
        # write base64 image
        User.write({'image': 'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='})
        write_date_after = User.write_date

        # Ensure that write_date is not equal before and after record update.
        self.assertNotEquals(write_date_before, write_date_after)
