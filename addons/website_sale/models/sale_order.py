# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    website_order_line = fields.One2many(
        'sale.order.line', 'order_id',
        string='Order Lines displayed on Website', readonly=True,
        help='Order Lines to be displayed on the website. They should not be used for computation purpose.',
    )
    cart_quantity = fields.Integer(compute='_compute_cart_info', string='Cart Quantity')
    only_services = fields.Boolean(compute='_compute_cart_info', string='Only Services')
    is_abandoned_cart = fields.Boolean('Abandoned Cart', compute='_compute_abandoned_cart', search='_search_abandoned_cart')
    cart_recovery_email_sent = fields.Boolean('Cart recovery email already sent')
    website_id = fields.Many2one('website', related='partner_id.website_id', string='Website',
                                 help='Website through which this order was placed.',
                                 store=True, readonly=True)

    @api.multi
    @api.depends('website_order_line.product_uom_qty', 'website_order_line.product_id')
    def _compute_cart_info(self):
        for order in self:
            order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_qty')))
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)

    @api.multi
    @api.depends('team_id.team_type', 'date_order', 'order_line', 'state', 'partner_id')
    def _compute_abandoned_cart(self):
        abandoned_delay = self.website_id and self.website_id.cart_abandoned_delay or 1.0
        abandoned_datetime = datetime.utcnow() - relativedelta(hours=abandoned_delay)
        for order in self:
            domain = order.date_order <= abandoned_datetime and order.team_id.team_type == 'website' and order.state == 'draft' and order.partner_id.id != self.env.ref('base.public_partner').id and order.order_line
            order.is_abandoned_cart = bool(domain)

    def _search_abandoned_cart(self, operator, value):
        abandoned_delay = self.website_id and self.website_id.cart_abandoned_delay or 1.0
        abandoned_datetime = fields.Datetime.to_string(datetime.utcnow() - relativedelta(hours=abandoned_delay))
        abandoned_domain = expression.normalize_domain([
            ('date_order', '<=', abandoned_datetime),
            ('team_id.team_type', '=', 'website'),
            ('state', '=', 'draft'),
            ('partner_id.id', '!=', self.env.ref('base.public_partner').id),
            ('order_line', '!=', False)
        ])
        # is_abandoned domain possibilities
        if (operator not in expression.NEGATIVE_TERM_OPERATORS and value) or (operator in expression.NEGATIVE_TERM_OPERATORS and not value):
            return abandoned_domain
        return expression.distribute_not(abandoned_domain)  # negative domain

    @api.multi
    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        self.ensure_one()
        product = self.env['product.product'].browse(product_id)

        # split lines with the same product if it has untracked attributes
        if product and product.mapped('attribute_line_ids').filtered(lambda r: not r.attribute_id.create_variant) and not line_id:
            return self.env['sale.order.line']

        domain = [('order_id', '=', self.id), ('product_id', '=', product_id)]
        if line_id:
            domain += [('id', '=', line_id)]
        return self.env['sale.order.line'].sudo().search(domain)

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0):
        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        product_context.setdefault('lang', order.partner_id.lang)
        product_context.update({
            'partner': order.partner_id.id,
            'quantity': qty,
            'date': order.date_order,
            'pricelist': order.pricelist_id.id,
        })
        product = self.env['product.product'].with_context(product_context).browse(product_id)
        pu = product.price
        if order.pricelist_id and order.partner_id:
            order_line = order._cart_find_product_line(product.id)
            if order_line:
                pu = self.env['account.tax']._fix_tax_included_price_company(pu, product.taxes_id, order_line[0].tax_id, self.company_id)

        return {
            'product_id': product_id,
            'product_uom_qty': qty,
            'order_id': order_id,
            'product_uom': product.uom_id.id,
            'price_unit': pu,
        }

    @api.multi
    def _get_line_description(self, order_id, product_id, attributes=None):
        if not attributes:
            attributes = {}

        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        product_context.setdefault('lang', order.partner_id.lang)
        product = self.env['product.product'].with_context(product_context).browse(product_id)

        name = product.display_name

        # add untracked attributes in the name
        untracked_attributes = []
        for k, v in attributes.items():
            # attribute should be like 'attribute-48-1' where 48 is the product_id, 1 is the attribute_id and v is the attribute value
            attribute_value = self.env['product.attribute.value'].sudo().browse(int(v))
            if attribute_value and not attribute_value.attribute_id.create_variant:
                untracked_attributes.append(attribute_value.name)
        if untracked_attributes:
            name += '\n%s' % (', '.join(untracked_attributes))

        if product.description_sale:
            name += '\n%s' % (product.description_sale)

        return name

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, attributes=None, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        SaleOrderLineSudo = self.env['sale.order.line'].sudo()

        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_lines = self._cart_find_product_line(product_id, line_id, **kwargs)
            order_line = order_lines and order_lines[0]

        # Create line if no line with product_id can be located
        if not order_line:
            values = self._website_product_id_change(self.id, product_id, qty=1)
            values['name'] = self._get_line_description(self.id, product_id, attributes=attributes)
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1

        # compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)

        # Remove zero of negative lines
        if quantity <= 0:
            order_line.unlink()
        else:
            # update line
            values = self._website_product_id_change(self.id, product_id, qty=quantity)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                order = self.sudo().browse(self.id)
                product_context = dict(self.env.context)
                product_context.setdefault('lang', order.partner_id.lang)
                product_context.update({
                    'partner': order.partner_id.id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
                product = self.env['product.product'].with_context(product_context).browse(product_id)
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    order_line._get_display_price(product),
                    order_line.product_id.taxes_id,
                    order_line.tax_id,
                    self.company_id
                )

            order_line.write(values)

        return {'line_id': order_line.id, 'quantity': quantity}

    def _cart_accessories(self):
        """ Suggest accessories based on 'Accessory Products' of products in cart """
        for order in self:
            accessory_products = order.website_order_line.mapped('product_id.accessory_product_ids').filtered(lambda product: product.website_published)
            accessory_products -= order.website_order_line.mapped('product_id')
            return random.sample(accessory_products, len(accessory_products))

    @api.multi
    def action_recovery_email_send(self):
        composer_form_view_id = self.env.ref('mail.email_compose_message_wizard_form').id
        try:
            default_template = self.env.ref('website_sale.mail_template_sale_cart_recovery', raise_if_not_found=False)
            default_template_id = default_template.id if default_template else False
            template_id = self.website_id and self.website_id.cart_recovery_mail_template_id.id or default_template_id
        except:
            template_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': composer_form_view_id,
            'target': 'new',
            'context': {
                'default_composition_mode': 'mass_mail',
                'default_res_id': self.ids[0],
                'default_model': 'sale.order',
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'website_sale_send_recovery_email': True,
                'active_ids': self.ids,
            },
        }

    @api.multi
    def send_order_confirmation_mail(self, transaction=False):
        # send order confirmation mail when payment done through the ecommerce
        super(SaleOrder, self).send_order_confirmation_mail(transaction=transaction)
        confirmation_template = self.env['ir.config_parameter'].sudo().get_param('website_sale.ecommerce_confirmation_template', False)
        if confirmation_template:
            for order in self.filtered(lambda so: so.team_id.team_type == 'website'):
                order.with_context(transaction=transaction, has_carrier=hasattr(order, 'carrier_id')).message_post_with_template(int(confirmation_template), notif_layout='mail.mail_notification_light')


    def _set_demo_create_date(self, create_date):
        self.env.cr.execute("""UPDATE sale_order SET create_date=%s WHERE id IN %s """, (create_date, tuple(self.ids)))
        self.modified(['create_date'])
        if self.env.recompute and self.env.context.get('recompute', True):
            self.recompute()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    name_short = fields.Char(compute="_compute_name_short")

    @api.multi
    @api.depends('product_id.display_name')
    def _compute_name_short(self):
        """ Compute a short name for this sale order line, to be used on the website where we don't have much space.
            To keep it short, instead of using the first line of the description, we take the product name without the internal reference.
        """
        for record in self:
            record.name_short = record.product_id.with_context(display_default_code=False).display_name

    def get_description_following_lines(self):
        return self.name.splitlines()[1:]
