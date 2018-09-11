odoo.define('web_editor.field.html.iframe', function (require) {
'use strict';

var core = require('web.core');
var FieldTextHtmlSimple = require('web_editor.field.html');

var qweb = core.qweb;


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
        options.iframeCssAssets = this.nodeOptions.iframeCssAssets;
        options.snippets = this.nodeOptions.snippets;
        return options;
    },
    /**
     * @override
     */
    _textToHtml: function () {
        var html = this._super.apply(this, arguments);
        if (this.nodeOptions.wrapper) {
            html = $(qweb.render(this.nodeOptions.wrapper))
                .find('#wrapper').html(html)
                .end().prop('outerHTML');
        }
        return html;
    },
    /**
     * @override
     */
    _getValue: function () {
        var html = this._super();
        if (this.nodeOptions.wrapper) {
            html = $(html).find('#wrapper').html();
        }
        return html;
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
