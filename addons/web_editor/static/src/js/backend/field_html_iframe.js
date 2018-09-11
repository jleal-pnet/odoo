odoo.define('web_editor.field.html.iframe', function (require) {
'use strict';

var FieldTextHtmlSimple = require('web_editor.field.html');

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
        options.snippets = this.nodeOptions.snippets;
        options.iframeCssAssets = this.nodeOptions.iframeCssAssets;
        return options;
    },
});

console.error('todo: readonly in iframe');
// mass_mailing: /mass_mailing/static/src/css/basic_theme_readonly.css

console.error('insert js mass_mailing');
/*

mass_mailing/static/src/js/mass_mailing_editor.js
mass_mailing.FieldTextHtmlInline

To remove: 

FieldTextHtmlInline
FieldTextHtmlPopupContent

*/

return FieldTextHtmlIframe;
});
