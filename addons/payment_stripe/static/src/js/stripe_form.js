odoo.define('payment_stripe.stripe_form', function(require) {
"use strict";

var payment = require('payment.payment_form');

payment.include({

    events: _.extend({}, payment.prototype.events, {
        'click .stripe_payment_type': 'paymentTypeSelect'
    }),

    init: function(parent, options) {
        this._super.apply(this, arguments);
        if ($('.o_payment_form').find('input[type="radio"]:checked').length && $('.o_payment_form').find('input[type="radio"]:checked').data().provider == 'stripe') {
            $('.o_payment_form').find('.stripe_payment_type').removeClass('d-none');
        }
    },

    radioClickEvent: function (ev) {
        this._super.apply(this, arguments);
        if (ev.currentTarget.dataset.provider == 'stripe') {
            this.$el.find('.stripe_payment_type').removeClass('d-none');
        } else {
            this.$el.find('.stripe_payment_type, .o_stripe_payment_type').addClass('d-none');
        }
    },

    paymentTypeSelect: function (ev) {
        var payment_type = $(ev.currentTarget.selectedOptions).val().toLowerCase().replace(/\ /g, '_');
        $('#payment_error').remove();
        this.$el.find('.o_stripe_payment_type').addClass('d-none');
        this.$el.find('.o_stripe_' + payment_type).removeClass('d-none');
    },
});

});
