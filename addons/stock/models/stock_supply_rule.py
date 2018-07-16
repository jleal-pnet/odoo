# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.exceptions import UserError


class StockSupplyRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _name = 'stock.supply.rule'
    _description = "Stock Rule"
    _order = "sequence, name"

    name = fields.Char(
        'Name', required=True, translate=True,
        help="This field will fill the packing origin and the name of its moves")
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the rule without removing it.")
    group_propagation_option = fields.Selection([
        ('none', 'Leave Empty'),
        ('propagate', 'Propagate'),
        ('fixed', 'Fixed')], string="Propagation of Procurement Group", default='propagate')
    group_id = fields.Many2one('procurement.group', 'Fixed Procurement Group')
    action = fields.Selection(
        selection=[('pull', 'Pull From'), ('push', 'Push To'), ('pull_push', 'Pull & Push')], string='Action',
        required=True)
    sequence = fields.Integer('Sequence', default=20)
    company_id = fields.Many2one('res.company', 'Company',
        default=lambda self: self.env.user.company_id)
    location_id = fields.Many2one('stock.location', 'Destination Location', required=True)
    location_src_id = fields.Many2one('stock.location', 'Source Location')
    route_id = fields.Many2one('stock.location.route', 'Route', ondelete='cascade')
    procure_method = fields.Selection([
        ('make_to_stock', 'Take From Stock'),
        ('make_to_order', 'Trigger Another Rule')], string='Move Supply Method',
        default='make_to_stock', required=True,
        help="""Create Procurement: A procurement will be created in the source location and the system will try to find a rule to resolve it. The available stock will be ignored.
             Take from Stock: The products will be taken from the available stock.""")
    route_sequence = fields.Integer('Route Sequence', related='route_id.sequence', store=True)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True)
    delay = fields.Integer('Delay', default=0, help="The expected date of the created transfer will be computed based on this delay.")
    partner_address_id = fields.Many2one('res.partner', 'Partner Address', help="Address where goods should be delivered. Optional.")
    propagate = fields.Boolean(
        'Propagate cancel and split', default=True,
        help="When ticked, if the move is splitted or cancelled, the next move will be too.")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    propagate_warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse to Propagate',
        help="The warehouse to propagate on the created move/procurement, which can be different of the warehouse this rule is for (e.g for resupplying rules from another warehouse)")
    auto = fields.Selection([
        ('manual', 'Manual Operation'),
        ('transparent', 'Automatic No Step Added')], string='Automatic Move',
        default='manual', index=True, required=True,
        help="The 'Manual Operation' value will create a stock move after the current one. "
             "With 'Automatic No Step Added', the location is replaced in the original move.")
    rule_message = fields.Html(compute='_compute_action_message')

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        """ Modify locations to the default picking type's locations source and
        destination.
        """
        self.location_src_id = self.picking_type_id.default_location_src_id.id
        self.location_id = self.picking_type_id.default_location_dest_id.id

    @api.onchange('route_id', 'company_id')
    def _onchange_route(self):
        """ If a route is set and it exists a route company, ensure that the
        rule's company is the same than the route's company.
        """
        company_id = self.route_id.company_id
        if company_id:
            self.company_id = company_id
            if self.picking_type_id.warehouse_id.company_id != company_id:
                self.picking_type_id = False
        domain = {'company_id': company_id and [('id', '=', company_id.id)] or []}
        return {'domain': domain}

    def _get_message_values(self):
        """ Return the source, destination and picking_type apply on a stock
        rule. The purpose of this function is to avoid code duplication in
        _get_message_dict functions since it often require those data.
        """
        source = self.location_src_id and self.location_src_id.display_name or _('Source Location')
        destination = self.location_id and self.location_id.display_name or _('Destination Location')
        operation = self.picking_type_id and self.picking_type_id.name or _('Operation Type')
        return source, destination, operation

    def _get_message_dict(self):
        """ Return a dict with the different possible message used for the
        rule message. It should return one message for each stock.supply.rule action
        (except push and pull). This function is override in mrp and
        purchase_stock in order to complete the dictionary.
        """
        message_dict = {}
        source, destination, operation = self._get_message_values()
        if self.action in ('push', 'pull', 'pull_push'):
            suffix = ""
            if self.procure_method == 'make_to_order' and self.location_src_id:
                suffix = _("<br>A need is created in <b>%s</b> and a rule will be triggered to fulfill it.") % (source)
            message_dict = {
                'pull': _('When products are needed in <b>%s</b>, <br/> <b>%s</b> are created from <b>%s</b> to fulfill the need.') % (destination, operation, source) + suffix,
                'push': _('When products arrive in <b>%s</b>, <br/> <b>%s</b> are created to send them in <b>%s</b>.') % (source, operation, destination)
            }
        return message_dict

    @api.depends('action', 'location_id', 'location_src_id', 'picking_type_id', 'procure_method')
    def _compute_action_message(self):
        """ Generate dynamicaly a message that describe the rule purpose to the
        end user.
        """
        for rule in self.filtered(lambda rule: rule.action):
            message_dict = rule._get_message_dict()
            message = message_dict.get(rule.action) and message_dict[rule.action] or ""
            if rule.action == 'pull_push':
                message = message_dict['pull'] + "<br/><br/>" + message_dict['push']
            rule.rule_message = message

    def _apply(self, move):
        """ Apply a rule on a move.
        If the rule is 'no step added' it will modify the destination location
        on the move.
        If the rule is 'manual operation' it will generate a new move in order
        to complete the section define by the rule.
        """
        new_date = (datetime.strptime(move.date_expected, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=self.delay)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.auto == 'transparent':
            move.write({
                'date': new_date,
                'date_expected': new_date,
                'location_dest_id': self.location_id.id})
            # avoid looping if a push rule is not well configured; otherwise call again push_apply to see if a next step is defined
            if self.location_id != move.location_dest_id:
                # TDE FIXME: should probably be done in the move model IMO
                move._push_apply()
        else:
            new_move_vals = self._prepare_move_copy_values(move, new_date)
            new_move = move.copy(new_move_vals)
            move.write({'move_dest_ids': [(4, new_move.id)]})
            new_move._action_confirm()

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = {
                'origin': move_to_copy.origin or move_to_copy.picking_id.name or "/",
                'location_id': move_to_copy.location_dest_id.id,
                'location_dest_id': self.location_id.id,
                'date': new_date,
                'date_expected': new_date,
                'company_id': self.company_id.id,
                'picking_id': False,
                'picking_type_id': self.picking_type_id.id,
                'propagate': self.propagate,
                'warehouse_id': self.warehouse_id.id,
            }
        return new_move_vals

    def _run_pull(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        if not self.location_src_id:
            msg = _('No source location defined on stock rule: %s!') % (self.name, )
            raise UserError(msg)

        # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
        # Search if picking with move for it exists already:
        group_id = False
        if self.group_propagation_option == 'propagate':
            group_id = values.get('group_id', False) and values['group_id'].id
        elif self.group_propagation_option == 'fixed':
            group_id = self.group_id.id

        data = self._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        # Since action_confirm launch following procurement_group we should activate it.
        move = self.env['stock.move'].sudo().with_context(force_company=data.get('company_id', False)).create(data)
        move._action_confirm()
        return True

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        date_expected = (datetime.strptime(values['date_planned'], DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(days=self.delay or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_left = product_qty
        return {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or values['company_id'].id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.partner_address_id.id or (values.get('group_id', False) and values['group_id'].partner_id.id) or False,
            'location_id': self.location_src_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.propagate,
            'priority': values.get('priority', "1"),
        }

    def _log_next_activity(self, product_id, note):
        existing_activity = self.env['mail.activity'].search([('res_id', '=',  product_id.product_tmpl_id.id), ('res_model_id', '=', self.env.ref('product.model_product_template').id),
                                                              ('note', '=', note)])
        if not existing_activity:
            # If the user deleted todo activity type.
            try:
                activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            except:
                activity_type_id = False
            self.env['mail.activity'].create({
                'activity_type_id': activity_type_id,
                'note': note,
                'user_id': product_id.responsible_id.id,
                'res_id': product_id.product_tmpl_id.id,
                'res_model_id': self.env.ref('product.model_product_template').id,
            })

    def _make_po_get_domain(self, values, partner):
        return ()


