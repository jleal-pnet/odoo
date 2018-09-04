# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.tools.misc import mod10r

import werkzeug.urls

def _is_l10n_ch_postal(account_ref):
    """ Returns True iff the string account_ref is a valid postal account number,
    i.e. it only contains ciphers and is last cipher is the result of a recursive
    modulo 10 operation ran over the rest of it.
    """
    if re.match('\d+$', account_ref or ''):
        account_ref_without_check = account_ref[:-1]
        return mod10r(account_ref_without_check) == account_ref
    return False


class ResBank(models.Model):
    _inherit = 'res.bank'

    l10n_ch_postal_chf = fields.Char(string='CHF ISR reference', help='The postal reference of the bank, used to generate ISR payment slips in CHF.')
    l10n_ch_postal_eur = fields.Char(string='EUR ISR reference', help='The postal reference of the bank, used to generate ISR payment slips in EUR.')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_ch_postal = fields.Char(string='ISR reference', help='The ISR number of the company within the bank')

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(('postal', _('Postal')))
        return rslt

    @api.model
    def retrieve_acc_type(self, acc_number):
        """ Overridden method enabling the recognition of swiss postal bank
        account numbers.
        """
        if _is_l10n_ch_postal(acc_number):
            return 'postal'
        else:
            return super(ResPartnerBank, self).retrieve_acc_type(acc_number)

    @api.onchange('acc_number')
    def _onchange_set_l10n_ch_postal(self):
        if self.acc_type == 'iban':
            self.l10n_ch_postal = self._retrieve_l10n_ch_postal(self.sanitized_acc_number)
        else:
            self.l10n_ch_postal = self.sanitized_acc_number

    @api.model
    def _retrieve_l10n_ch_postal(self, iban):
        """ Reads a swiss postal account number from a an IBAN and returns it as
        a string. Returns None if no valid postal account number was found, or
        the given iban was not from Switzerland.
        """
        if iban[:2] == 'CH':
            #the IBAN corresponds to a swiss account
            if _is_l10n_ch_postal(iban[-12:]):
                return iban[-12:]
        return None

    @api.model
    def build_swiss_code_url(self, amount, comment, debitor, ref_type):
        communication = ""
        if comment:
            communication = (comment[:137] + '...') if len(comment) > 140 else comment
        number = [int(s) for s in self.company_id.street.split() if s.isdigit()]
        number_deb = [int(s) for s in debitor.street.split() if s.isdigit()]

        qr_code_string = 'SPC\n0100\n1\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s' % (
                          self.acc_number,
                          self.company_id.name,
                          self.company_id.street.replace(str(number[0]),'').strip(),
                          number[0],
                          self.company_id.zip,
                          self.company_id.city,
                          self.company_id.country_id.code,
                          amount,
                          self.currency_id.name,
                          debitor.name,
                          debitor.street.replace(str(number_deb[0]),'').strip(),
                          number_deb[0],
                          debitor.zip,
                          debitor.city,
                          debitor.country_id.code,
                          ref_type,
                          communication)
        qr_code_url = '/report/barcode/?type=%s&value=%s&width=%s&height=%s&humanreadable=1' % ('QR', werkzeug.url_quote_plus(qr_code_string), 256, 256)
        return qr_code_url

    @api.multi 
    def _validate_qr_code_arguments(self):
        for bank in self:
            if bank.currency_id.name == False:
                currency = bank.company_id.currency_id
            else:
                currency = bank.currency_id
            bank.qr_code_valid = (bank.bank_bic
                                            and bank.company_id.name
                                            and bank.acc_number
                                            and (currency.name == 'EUR'))