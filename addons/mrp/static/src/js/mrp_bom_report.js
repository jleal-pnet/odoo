odoo.define('mrp.mrp_bom_report', function (require) {
'use strict';

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var session = require('web.session');
var stock_report_generic = require('stock.stock_report_generic');

var QWeb = core.qweb;

var MrpBomReport = stock_report_generic.extend({
    events: {
        'click .o_mrp_bom_unfoldable': '_onClickUnfold',
        'click .o_mrp_bom_foldable': '_onClickFold',
        'click .o_mrp_bom_action': '_onClickAction',
    },
    get_html: function() {
        var self = this;
        var defs = [];
        var args = [
            this.given_context.active_id,
            this.given_context.searchQty || 1,
            this.given_context.searchVariant,
        ];
        return this._rpc({
                model: 'mrp.bom.report',
                method: 'get_html',
                args: args
            })
            .then(function (result) {
                self.data = result;
                defs.push(self.update_cp());
                return $.when.apply($, defs);
            });
    },
    set_html: function() {
        var self = this;
        return this._super().then(function () {
            self.$el.html(self.data.lines);
            self.renderSearch();
            self.update_cp();
        });
    },
    render_html: function(event, $el, result){
        $el.after(result);
        $(event.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
        this._reload_report_type();
    },
    get_bom: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('id');
      var productID = $parent.data('product_id');
      var lineID = $parent.data('line');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      return this._rpc({
              model: 'mrp.bom.report',
              method: 'get_bom',
              args: [
                  activeID,
                  productID,
                  parseFloat(qty),
                  lineID,
                  level + 1
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    get_operations: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('bom-id');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      return this._rpc({
              model: 'mrp.bom.report',
              method: 'get_operations',
              args: [
                  activeID,
                  parseFloat(qty),
                  level + 1
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    update_cp: function () {
        var status = {
            cp_content: {
                $buttons: this.$buttonPrint,
                $searchview_buttons: this.$searchView
            },
        };
        return this.update_control_panel(status);
    },
    renderSearch: function () {
        this.$buttonPrint = $(QWeb.render('mrp.button'));
        this.$buttonPrint.on('click', this._onClickPrint.bind(this));
        this.$searchView = $(QWeb.render('mrp.report_bom_search', _.omit(this.data, 'lines')));
        this.$searchView.find('.o_mrp_bom_report_qty').on('change', this._onChangeQty.bind(this));
        this.$searchView.find('.o_mrp_bom_report_variants').on('change', this._onChangeVariants.bind(this));
        this.$searchView.find('.o_mrp_bom_report_type').on('change', this._onChangeType.bind(this));
    },
    _onClickPrint: function () {
        var childBomIDs = _.map(this.$el.find('.o_mrp_bom_foldable').closest('tr'), function (el) {
            return $(el).data('id');
        });
        framework.blockUI();
        var kwargs = {
            searchQty: this.given_context.searchQty || 1,
            child_bom_ids: JSON.stringify(childBomIDs),
            report_structure: this.given_context.report_type || 'all',
        };
        if (this.given_context.searchVariant) {
            kwargs.searchVariant = this.given_context.searchVariant;
        }
        session.get_file({
            url: '/stock/pdf/mrp_bom_report/mrp_bom_report/' + this.given_context.active_id,
            data: kwargs,
            complete: framework.unblockUI,
            error: crash_manager.rpc_error.bind(crash_manager),
        });
    },
    _onChangeQty: function (ev) {
        var qty = $(ev.currentTarget).val().trim();
        if (qty) {
            this.given_context.searchQty = parseFloat(qty);
            this._reload();
        }
    },
    _onChangeType: function (ev) {
        var report_type = $("option:selected", $(ev.currentTarget)).data('type');
        this.given_context.report_type = report_type;
        this._reload_report_type();
    },
    _onChangeVariants: function (ev) {
        this.given_context.searchVariant = $(ev.currentTarget).val();
        this._reload();
    },
    _onClickUnfold: function (ev) {
        var redirect_function = $(ev.currentTarget).data('function');
        this[redirect_function](ev);
    },
    _onClickFold: function (ev) {
        this._removeLines($(ev.currentTarget).closest('tr'));
        $(ev.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
    },
    _onClickAction: function (ev) {
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: $(ev.currentTarget).data('model'),
            res_id: $(ev.currentTarget).data('res-id'),
            views: [[false, 'form']],
            target: 'current'
        });
    },
    _reload: function () {
        var self = this;
        return this.get_html().then(function () {
            self.$el.html(self.data.lines);
            self._reload_report_type();
        });
    },
    _reload_report_type: function () {
        this.$('.o_mrp_bom_cost').show();
        this.$('.o_mrp_prod_cost').show();
        if (this.given_context.report_type === 'bom_structure') {
            this.$('.o_mrp_bom_cost').hide();
        }
        if (this.given_context.report_type === 'bom_cost') {
            this.$('.o_mrp_prod_cost').hide();
        }
    },
    _removeLines: function ($el) {
        var self = this;
        var activeID = $el.data('id');
        _.each(this.$('tr[parent_id='+ activeID +']'), function (parent) {
            var $parent = self.$(parent);
            var $el = self.$('tr[parent_id='+ $parent.data('id') +']');
            if ($el.length) {
                self._removeLines($parent);
            }
            $parent.remove();
        });
    },
});

core.action_registry.add('mrp_bom_report', MrpBomReport);
return MrpBomReport;

});
