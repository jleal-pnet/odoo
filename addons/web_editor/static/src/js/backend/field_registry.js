odoo.define('web_editor.backend', function (require) {
'use strict';

var fieldHtml = require('web_editor.field.html');
var fieldHtmlIframe = require('web_editor.field.html.iframe');

var field_registry = require('web.field_registry');

field_registry
    .add('html', fieldHtml)
    .add('html_frame', fieldHtmlIframe);

});
