# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.tools.xml_utils import _check_with_xsd
from odoo.exceptions import UserError
from odoo.addons.l10n_be_edi.models.account_invoice import PATH_TO_XSD
from odoo.osv import expression


class ImportInvoiceXmlWizard(models.TransientModel):
    _inherit = 'account.invoice.xml.import'

    @api.model
    def _get_ubl_namespaces(self, tree):
        ''' If the namespace is declared with xmlns='...', the namespaces map contains the 'None' key that causes an
        TypeError: empty namespace prefix is not supported in XPath
        Then, we need to remap arbitrarily this key.

        :param tree: An instance of etree.
        :return: The namespaces map without 'None' key.
        '''
        namespaces = tree.nsmap
        namespaces['inv'] = namespaces.pop(None)
        return namespaces

    @api.model
    def _detect_ubl_2_1(self, tree):
        # Quick check the tree looks like an UBL 2.1 file.
        flag = tree.tag == '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice'
        error = None

        # Check the xsd validity.
        with tools.file_open(PATH_TO_XSD, "rb") as xsd:
            try:
                _check_with_xsd(tree, xsd)
            except UserError:
                error = _('File is invalid.')
        return {'flag': flag, 'error': error}

    @api.model
    def _decode_ubl_2_1(self, tree):
        namespaces = self._get_ubl_namespaces(tree)

        values = {}

        # Reference
        elements = tree.xpath('//cbc:ID', namespaces=namespaces)
        values['reference'] = elements and elements[0].text or None

        # Date + Due Date
        elements = tree.xpath('//cbc:IssueDate', namespaces=namespaces)
        values['date'] = elements and elements[0].text or None
        elements = tree.xpath('//cbc:PaymentDueDate', namespaces=namespaces)
        values['date_due'] = elements and elements[0].text or None

        # Type
        elements = tree.xpath('//cbc:InvoiceTypeCode', namespaces=namespaces)
        type_code = elements and elements[0].text or None
        values['type'] = 'in_refund' if type_code == '381' else 'in_invoice'

        # Currency
        elements = tree.xpath('//cbc:DocumentCurrencyCode', namespaces=namespaces)
        currency_code = elements and elements[0].text or ''
        currency = self.env['res.currency'].search([('name', '=', currency_code.upper())], limit=1)
        values['currency_id'] = currency and currency.id or None

        # Partner
        partner_element = tree.xpath('//cac:AccountingSupplierParty/cac:Party/cac:Contact', namespaces=namespaces)
        if partner_element:
            partner_element = partner_element[0]
            elements = partner_element.xpath('cbc:Name', namespaces=namespaces)
            partner_name = elements and elements[0].text or None
            elements = partner_element.xpath('cbc:Telephone', namespaces=namespaces)
            partner_telephone = elements and elements[0].text or None
            elements = partner_element.xpath('cbc:ElectronicMail', namespaces=namespaces)
            partner_mail = elements and elements[0].text or None

            domains = []
            if partner_name:
                domains.append([('name', 'ilike', partner_name)])
            if partner_telephone:
                domains.append([('phone', '=', partner_telephone), ('mobile', '=', partner_telephone)])
            if partner_mail:
                domains.append([('email', '=', partner_mail)])
            if domains:
                partner = self.env['res.partner'].search(expression.OR(domains), limit=1)
                values['partner_id'] = partner and partner.id or None

        # Create invoice
        ctx = dict(self._context, type=values['type'])
        invoice = self.env['account.invoice'].with_context(ctx).create(values)
        ctx['journal_id'] = invoice.journal_id.id

        # Regenerate PDF
        elements = tree.xpath('//cac:AdditionalDocumentReference', namespaces=namespaces)
        if elements:
            attachment_name = elements[0].xpath('cbc:ID', namespaces=namespaces)[0].text
            attachment_data = elements[0].xpath('cac:Attachment//cbc:EmbeddedDocumentBinaryObject', namespaces=namespaces)[0].text
            self.env['ir.attachment'].create({
                'name': attachment_name,
                'res_id': invoice.id,
                'res_model': 'account.invoice',
                'datas': attachment_data,
                'datas_fname': attachment_name,
                'type': 'binary',
            })

        # Lines
        lines_elements = tree.xpath('//cac:InvoiceLine', namespaces=namespaces)
        for eline in lines_elements:
            line_values = {}

            # Quantity
            elements = eline.xpath('cbc:InvoicedQuantity', namespaces=namespaces)
            quantity = elements and float(elements[0].text) or 1.0
            line_values['quantity'] = quantity

            # Price Unit
            elements = eline.xpath('cac:Price/cbc:PriceAmount', namespaces=namespaces)
            line_values['price_unit'] = elements and float(elements[0].text) or 0.0

            # Name
            elements = eline.xpath('cac:Item/cbc:Description', namespaces=namespaces)
            line_values['name'] = elements and elements[0].text or ''

            # Product
            elements = eline.xpath('cac:Item/cac:SellersItemIdentification/cbc:ID', namespaces=namespaces)
            product_code = elements and elements[0].text or None
            elements = eline.xpath('cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID=\'GTIN\']', namespaces=namespaces)
            product_ean13 = elements and elements[0].text or None
            domains = []
            if product_code:
                domains.append([('default_code', '=', product_code)])
            if product_ean13:
                domains.append([('ean13', '=', product_ean13)])
            if domains:
                product = self.env['product.product'].search(expression.OR(domains), limit=1)
                line_values['product_id'] = product and product.id or None

            # Taxes
            taxes_elements = eline.xpath('cac:Item/cac:TaxSubtotal/cac:TaxCategory', namespaces=namespaces)
            taxes = []
            for etax in taxes_elements:
                # Not yet supported
                pass

            line_values['invoice_id'] = invoice.id

            self.env['account.invoice.line'].with_context(ctx).create(line_values)

        return invoice

    @api.model
    def _get_xml_decoders(self):
        # Override
        ubl_decoders = [('UBL 2.1', self._detect_ubl_2_1, self._decode_ubl_2_1)]
        return super(ImportInvoiceXmlWizard, self)._get_xml_decoders() + ubl_decoders
