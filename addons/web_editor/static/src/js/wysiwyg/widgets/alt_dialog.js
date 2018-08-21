odoo.define('wysiwyg.widgets.AltDialog', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('wysiwyg.widgets.Dialog');

var _t = core._t;

/**
 * Let users change the alt & title of a media.
 */
var AltDialog = Dialog.extend({
    template: 'wysiwyg.widgets.alt',
    xmlDependencies: Dialog.prototype.xmlDependencies.concat(
        ['/web_editor/static/src/xml/editor.xml']
    ),

    /**
     * @constructor
     */
    init: function (parent, options, media) {
        this._super(parent, _.extend({}, {
            title: _t("Change media description and tooltip")
        }, options));
        this.media = media;
        this.alt = ($(this.media).attr('alt') || "").replace(/&quot;/g, '"');
        this.title = ($(this.media).attr('title') || "").replace(/&quot;/g, '"');
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    save: function () {
        var alt = this.$('#alt').val();
        var title = this.$('#title').val();
        $(this.media).attr('alt', alt ? alt.replace(/"/g, "&quot;") : null).attr('title', title ? title.replace(/"/g, "&quot;") : null);

        this.trigger('saved', {
            media: this.media,
        });
        return this._super.apply(this, arguments);
    },
});


return AltDialog;
});
