odoo.define('base.vat.vat_checker', function (require) {
    'use strict';

    var core = require('web.core');

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var _t = core._t;

    var rpc = require('web.rpc');
    var concurrency = require('web.concurrency');

    var VATChecker = AbstractField.extend({
        className: 'o_field_vat_checker',
        resetOnAnyFieldChange: true,
        currentValue: null,

        /**
         * @constructor
         * @see AbstractField.init
         */
        init: function () {
            this._super.apply(this, arguments);

            if (this.mode === 'edit') {
                this.currentValue = this.record.data.vat;
                this.dropPrevious = new concurrency.DropPrevious();
            }
        },

        /**
         * @override
         */
        start: function () {
            if (this.mode === 'edit') {
                this.$indicator = $('<i/>');
                this.$el.append(this.$indicator);
                if (this.record.data.vat_validation_state) this._setState(this.record.data.vat_validation_state);
            }

            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        reset: function (state) {
            var self = this;
            var oldVat = this.currentValue;
            var newVat = state.data.vat;
            this.currentValue = newVat;

            if (!newVat) {
                this._setState('hide');
            } else {
                if (oldVat !== newVat) {
                    self._setState('loading');

                    this._checkVATValidity(this._sanitizeVAT(newVat)).then(function (validity) {
                        if (validity.existing) self._setState('valid');
                        else {
                            if (validity.format) self._setState('unknown');
                            else {
                                self._setState('format', validity.expected_format);
                            }
                        }
                    });
                }
            }

            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        _checkVATValidity: function (vat) {
            var def = rpc.query({
                model: 'res.partner',
                method: 'check_vat_rpc',
                args: [vat],
            }, {
                shadow: true,
            });

            return this.dropPrevious.add(def);
        },

        /**
         * Sanitize search value by removing all not alphanumeric
         *
         * @param {string} search_value
         * @returns {string}
         * @private
         */
        _sanitizeVAT: function (search_value) {
            return search_value ? search_value.replace(/[^A-Za-z0-9]/g, '') : '';
        },

        _setState: function (state, extra_msg) {
            var classes, title, db_state;

            switch (state) {
                case 'valid':
                    classes = "fa fa-lg fa-check-circle text-success";
                    title = "VAT number is valid";
                    db_state = state;
                    break;
                case 'unknown':
                    classes = "fa fa-lg fa-question-circle text-warning";
                    title = "No company found with this VAT number";
                    db_state = state;
                    break;
                case 'format':
                    classes = "fa fa-lg fa-exclamation-triangle text-danger";
                    title = "Incorrect VAT number format";
                    if (extra_msg) title += ", expected format: %s";
                    db_state = state;
                    break;
                case 'loading':
                    classes = "fa fa-lg fa-spinner fa-spin text-muted";
                    title = "";
                    break;
            }

            this.$indicator
                .removeClass()
                .addClass(classes)
                .attr('title', _.str.sprintf(_t(title), extra_msg));

            if (db_state) this._setValue(db_state);
        },
    });

    fieldRegistry.add('vat_checker', VATChecker);

    return VATChecker;
});
