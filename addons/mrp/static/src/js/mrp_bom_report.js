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
    get_html: function(event) {
        var self = this;
        var defs = [];
        var $parent;
        var activeID = this.given_context.active_id;
        if(event){
            $parent = $(event.currentTarget).closest('tr');
            activeID = $parent.data('id');
        }
        var args = [
            activeID,
            this.given_context.searchQty || 1,
            this.given_context.searchVariant || false,
        ];
        if(event){
            var lineID = $parent.data('line');
            var qty = $parent.data('qty');
            var level = $parent.data('level') || 0;
            args.push(parseFloat(qty), lineID, level + 1);
        }
        return this._rpc({
                model: 'mrp.bom.report',
                method: 'get_html',
                args: args
            })
            .then(function (result) {
                if(! event){
                    self.data = result;
                    defs.push(self.update_cp());
                    return $.when.apply($, defs);
                }
                else{
                    $parent.after(result.lines);
                    $(event.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
                }
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
    _reload: function () {
        var self = this;
        return this.get_html().then(function () {
            self.$el.html(self.data.lines);
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
    },
    _onClickPrint: function () {
        var childBomIDs = _.map(this.$el.find('.o_mrp_bom_foldable').closest('tr'), function (el) {
            return $(el).data('id');
        });
        framework.blockUI();
        var values = {
            child_bom_ids: JSON.stringify(childBomIDs),
            searchQty: this.given_context.searchQty,
            searchVariant: this.given_context.searchVariant
        };

        session.get_file({
            url: '/stock/pdf/mrp_bom_report/mrp_bom_report/' + this.given_context.active_id,
            data: values,
            complete: framework.unblockUI,
            error: crash_manager.rpc_error.bind(crash_manager),
        });
    },
    _onChangeQty: function (ev) {
        var qty = $(ev.currentTarget).val().trim();
        if (qty) {
            this.given_context.searchQty = qty;
            this._reload();
        }
    },
    _onChangeVariants: function (ev) {
        this.given_context.searchVariant = $(ev.currentTarget).val();
        this._reload();
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
    _onClickUnfold: function (ev) {
        this.get_html(ev);
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
});

core.action_registry.add('mrp_bom_report', MrpBomReport);
return MrpBomReport;

});
