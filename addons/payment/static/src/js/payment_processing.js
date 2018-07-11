odoo.define('payment.processing', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var Ajax = require('web.ajax');
    var Core = require('web.core');
    var Qweb = Core.qweb;
    var _t = Core._t;

    return Widget.extend({
        /* Members */
        _payment_tx_ids: null,
        _pollCount: 0,
        /* Events */
        events: {

        },
        /* deps */
        xmlDependencies: ['/payment/static/src/xml/payment_processing.xml'],
        /* Widget overrides */
        init: function (parent, payment_tx_ids) {
            this._super.apply(this, arguments);
            //
            this._payment_tx_ids = payment_tx_ids;
        },
        start: function() {
            this.displayLoading();
            this.poll();
            return this._super.apply(this, arguments);
        },
        /* Methods */
        startPolling: function () {
            var timeout = 3000;
            //
            if(this._pollCount >= 10 && this._pollCount < 20) {
                timeout = 10000;
            }
            else if(this._pollCount >= 20) {
                timeout = 30000;
            }
            //
            setTimeout(this.poll.bind(this), timeout);
            this._pollCount ++;
        },
        poll: function () {
            var self = this;
            Ajax.jsonRpc('/payment/process/poll', 'call', {}).then(function(data) {
                if(data.success === true) {
                    self.processPolledData(data.transactions);
                }
                else {
                    switch(data.error) {
                        case "no_tx_found":
                               self.displayContent("payment.no_tx_found", {});
                            break;
                        default: // if an exception is raised
                                self.displayContent("payment.exception", {exception_msg: data.error});
                            break;
                    }
                }
                self.startPolling();
            }).fail(function(e) {
                self.displayContent("payment.rpc_error", {});
                self.startPolling();
            });
        },
        processPolledData: function (transactions) {
            var render_values = {
                'tx_draft': [],
                'tx_pending': [],
                'tx_authorized': [],
                'tx_done': [],
                'tx_cancel': [],
                'tx_error': [],
                'tx_refunding': [],
                'tx_refunded': [],
                'tx_unk': [],
            };
            // group the transaction according to their state
            transactions.forEach(tx => {
                var key = 'tx_' + tx.state;
                if((key in render_values) === false) {
                    key = 'tx_unk';
                }
                render_values[key].push(tx);
            });

            // if there's only one tx in the done state
            if(render_values['tx_done'].length == 1) {
                var unskippable_states = ['pending', 'authorized', 'draft', 'error', 'cancel'];
                var count = 0;

                // count how many tx are in an unskippable state
                unskippable_states.forEach(state => {
                    count += render_values['tx_' + state].length;
                });
                // if there's no tx in an unskippable state then we redirect the user to the return url
                if(count == 0) {
                    window.location = render_values['tx_done'][0].return_url;
                    return;
                }
            }

            this.displayContent("payment.display_tx_list", render_values);
        },
        displayContent: function (xmlid, render_values) {
            var html = Qweb.render(xmlid, render_values);
            this.$el.find('.o_payment_processing_content').html(html);
        },
        displayLoading: function () {
            this.displayContent("payment.process_polling_tx", {});
        },
    });
});