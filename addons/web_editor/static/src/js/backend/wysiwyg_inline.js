odoo.define('web_editor.wysiwyg.inline', function (require) {
'use strict';

var Wysiwyg = require('web_editor.wysiwyg');
var transcoder = require('web_editor.transcoder');

/*
 * add options style-inline
 **/
Wysiwyg.include({
    /*
     * @override
     */
    save: function () {
        if (this.options.styleInline) {
            if (this._summernote.invoke('codeview.isActivated')) {
                this._summernote.invoke('codeview.deactivate');
            }
            var $node = this._summernote.layoutInfo.editable;
            transcoder.attachmentThumbnailToLinkImg($node);
            transcoder.fontToImg($node);
            transcoder.classToStyle($node);
        }
        return this._super();
    },
});

});
