odoo.define('web_editor.field.html.iframe', function (require) {
'use strict';

var FieldTextHtmlSimple = require('web_editor.field.html');

// "/mass_mailing/field/email_template"

var FieldTextHtmlIframe = FieldTextHtmlSimple.extend({
    className: 'oe_form_field oe_form_field_html',
    supportedFieldTypes: ['html'],

    /**
     * change to be async because the target must be append in the DOM
     * to create iframe instance
     *
     * @override
     */
    _createWysiwygIntance: function () {
        setTimeout(this._super.bind(this));
    },
    /**
     * @override
     */
    _getWysiwygOptions: function () {
        var options = this._super();
        options.inIframe = true;
        options.snippets = true;
        // options.snippetsURL = this.nodeOptions.snippetsURL || '/web_editor/snippets' || '/mass_mailing/snippets';
        // options.iframeCssAssets = '';
        return options;
    },
});

return FieldTextHtmlIframe;
});
