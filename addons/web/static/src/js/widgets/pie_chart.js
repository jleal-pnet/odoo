odoo.define('web.PieChart', function (require) {
"use strict";

/**
 * This widget render a Pie Chart. It is used in the dashboard view.
 */
var Domain = require('web.Domain');
var viewRegistry = require('web.view_registry');
var Widget = require('web.Widget');
var widgetRegistry = require('web.widget_registry');

var PieChart = Widget.extend({
    className: 'o_pie_chart',
    /**
     * override
     *
     * @param {Widget} parent
     * @param {Object} record
     * @param {Object} node
     */
    init: function (parent, record, node) {
        this._super.apply(this, arguments);

        this.record = record;
        this.domain = record.domain;
        if (node.attrs.modifiers) {
            this.domain = this.domain.concat(
                Domain.prototype.stringToArray(node.attrs.modifiers.domain || '[]'));
            this.groupBy = node.attrs.modifiers.groupby.split(':')[0] || '';
            this.interval = node.attrs.modifiers.groupby.split(':')[1];
            this.measure = node.attrs.modifiers.measure || '';
            this.title = node.attrs.modifiers.title || this.measure || '';
            if (!_.contains(Object.keys(this.record.fields), this.groupBy)) {
                return;
            }

            this.groupByField = this.record.fields[this.groupBy];
            this.groupByType = this.groupByField.type;
        }
    },
    /**
     * override
     */
    willStart: function () {
        var self = this;
        var def1 = this._super.apply(this, arguments);
        var controllerContext;
        var subViewParams = {
            context: _.extend({}, this.record.context, controllerContext),
            domain: this.domain,
            groupBy: [],
            modelName: this.record.model,
            withControlPanel: false,
            hasSwitchButton: true,
            isEmbedded: true,
            additionalMeasures: this.additionalMeasures,
            mode: 'pie',
            title: this.title,
        };

        var SubView = viewRegistry.get('graph');
        var viewInfo = {
            arch: '<graph type="pie">' +
                    '<field name="' + this.groupBy + '" type="row"/>' +
                    //'<field name="date_deadline" interval="month" type="row"/>' +
                  '</graph>',
            fields: this.record.fields,
            viewFields: this.record.fieldsInfo.dashboard,
        };
        var subView = new SubView(viewInfo, subViewParams);
        var def2 = subView.getController(this).then(function (controller) {
            self.controller = controller;
            return self.controller.appendTo(document.createDocumentFragment());
        });
        return $.when(def1, def2);
    },
    /**
     * @override
     */
    start: function () {
        this.$el.append(this.controller.$el);
        return this._super.apply(this, arguments);
    },
    /**
     * Call `on_attach_callback` for each subview
     *
     * @override
     */
    on_attach_callback: function () {
        this.controller.on_attach_callback();
    },
});

widgetRegistry.add('pie_chart', PieChart);

return PieChart;

});
