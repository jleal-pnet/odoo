odoo.define('web_editor.summernote.plugin.Buttons', function (require) {
'use strict';

var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

var sOptions = $.summernote.options;

//--------------------------------------------------------------------------
// Override buttons, to have for eg: 'button.color' defined buttons
//--------------------------------------------------------------------------

var SummernoteButtons = sOptions.modules.buttons;
var NewSummernoteButtons = AbstractPlugin.extend(SummernoteButtons.prototype).extend({
    init: function () {
        this._super.apply(this, arguments);
        SummernoteButtons.apply(this, arguments);
    },
});

// override summernote default buttons
registry.add('buttons', NewSummernoteButtons);

return NewSummernoteButtons;

});
