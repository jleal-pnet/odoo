odoo.define('base.vat.vat_checker', function (require) {
'use strict';

var core = require('web.core');
var widgetRegistry = require('web.widget_registry');
var AbstractField = require('web.AbstractField');
// var fieldRegistry = require('web.field_registry');

var _t = core._t;

var VATChecker = AbstractField.extend({
    resetOnAnyFieldChange: true,

    jsLibs: [
        '/web/static/lib/jsvat/jsvat.js'
    ],

    /**
     * @constructor
     * Prepares the basic rendering of edit mode by setting the root to be a
     * div.dropdown.open.
     * @see FieldChar.init
     */
    init: function (parent, record, nodeInfo) {
        this._super.apply(this, [parent, 'vat', record]);

        if (record.mode === 'edit') {
            this.tagName = 'div';
            this.data = record.data;
            console.log(this.data);
        }
    },

    /**
     * @override
     */
    start: function () {
        this.$indicator = $('<i/>');
        this.$el.append(this.$indicator);
        return this._super.apply(this, arguments);
    },

    /**
     * @override
     */
    reset: function () {
        console.log('reset');
        console.log(arguments);
        return this._super.apply(this, arguments);
    },

   _reset: function () {
        console.log('_reset');
        console.log(arguments);
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _setValid: function () {

    },

    _setInvalid: function () {

    },

    _setUnknown: function () {

    },

    _setLoading: function () {

    },

});

widgetRegistry.add('vat_checker', VATChecker);

return VATChecker;
});
