odoo.define('iot.floatinput', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var registry = require('web.field_registry');

var FieldFloat = require('web.basic_fields').InputField

var IotFieldFloat = FieldFloat.extend({
    className: 'o_field_iot o_field_float o_field_number',  //or do some extends
    tagName: 'span',

    events: _.extend(FieldFloat.prototype.events, {
        'click .o_button_iot': '_onButtonClick',
    }),


    init: function () {
        this._super.apply(this, arguments);
        if (this.mode === 'edit') {
            this.tagName = 'div';
            this.className += ' o_input';
        }
    },

    _renderEdit: function() {
        this.$el.empty();

        // Prepare and add the input
        this._prepareInput(this.$input).appendTo(this.$el);

        var $button = $('<button>', {class: 'o_button_iot btn-sm btn-primary'}).text('Take measure');
        $button.appendTo(this.$el);
    },


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onButtonClick: function (ev) {
        var self = this;
        var ipField = this.nodeOptions.ip_field;
        var ip = this.record.data[ipField];
        
        var identifierField = this.nodeOptions.identifier_field;
        var identifier = this.record.data[identifierField];
        var composite_url = "http://"+ip+":8069/driverdetails/" + identifier;

        $.get(composite_url, function(data){
            self._setValue(data);
            self._render();
        });
        //this._rpc()
        //})
        //self = this;
        //$.ajax().then(function(result) {
        //    self.$input.value =
    }

})

registry.add('iot', IotFieldFloat);
});
