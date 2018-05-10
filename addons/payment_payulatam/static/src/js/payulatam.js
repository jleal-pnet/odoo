odoo.define('payment_payulatam.payulatam', function (require) {
"use strict";

var payment = require('payment.payment_form');

payment.include({

    /*
     * Once payment was being done by s2s or card has been added to the account and while user wants to make payment with
     * that token, it should show a cvc number input box to enter cvc number and make payment with it.
     *
     * @override
    */
    radioClickEvent: function (ev) {
        this._super.apply(this, arguments);
        this.$el.find('input[name=cvc_number]').addClass('hidden');
        $(ev.currentTarget).parent().next().removeClass('hidden');
    },
});
});
