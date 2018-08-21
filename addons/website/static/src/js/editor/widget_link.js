odoo.define('website.editor.link', function (require) {
'use strict';

var weWidgets = require('wysiwyg.widgets');
var wUtils = require('website.utils');

weWidgets.LinkDialog.include({
    /**
     * Allows the URL input to propose existing website pages.
     *
     * @override
     */
    start: function () {
        wUtils.autocompleteWithPages(this, this.$('input[name="url"]'));
        return this._super.apply(this, arguments);
    },
});
});
