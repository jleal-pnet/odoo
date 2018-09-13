odoo.define('web_editor.plugin.editor', function (require) {
'use strict';

var Plugins = require('web_editor.plugins');
var registry = require('web_editor.plugin.registry');

//--------------------------------------------------------------------------
// change editor to fix the twice undo (CTRL-Z) with odoo integration
//--------------------------------------------------------------------------

var NewSummernoteEditor = Plugins.editor.extend({
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
