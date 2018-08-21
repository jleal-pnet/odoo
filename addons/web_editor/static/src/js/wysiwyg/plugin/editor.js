odoo.define('web_editor.summernote.plugin.editor', function (require) {
'use strict';

var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

//--------------------------------------------------------------------------
// change editor to fix the twice undo (CTRL-Z) with odoo integration
//--------------------------------------------------------------------------

var SummernoteEditor = $.summernote.options.modules.editor;
var NewSummernoteEditor = AbstractPlugin.extend(SummernoteEditor.prototype).extend({
    init: function () {
        this._super.apply(this, arguments);
        SummernoteEditor.apply(this, arguments);
    },
    /**
     * @override
     */
    undo: function () {
        this.createRange();
        setTimeout(this._super.bind(this));
    },
});

// override summernote default editor
registry.add('editor', NewSummernoteEditor);

return NewSummernoteEditor;

});
