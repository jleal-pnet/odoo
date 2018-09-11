odoo.define('website.editor.menu', function (require) {
'use strict';

var Dialog = require('web.Dialog');
var Widget = require('web.Widget');
var core = require('web.core');
var WysiwygMultizone = require('web_editor.wysiwyg.multizone');
var snippetsEditor = require('web_editor.snippet.editor');

var _t = core._t;

var EditorMenu = Widget.extend({
    template: 'website.editorbar',
    xmlDependencies: ['/website/static/src/xml/website.editor.xml'],
    events: {
        'click button[data-action=save]': '_onSaveClick',
        'click button[data-action=cancel]': '_onCancelClick',
    },

    LOCATION_SEARCH: 'enable_editor',

    /**
     * @override
     */
    willStart: function () {
        this.$el = null; // temporary null to avoid hidden error (@see start)
        return this._super()
            .then(function () {
                var $wrapwrap = $('#wrapwrap');
                $wrapwrap.removeClass('o_editable'); // clean the dom before edition
                this.editable($wrapwrap).addClass('o_editable');
                this.wysiwyg = this._wysiwygInstance();
                return this.wysiwyg.attachTo($wrapwrap);
            }.bind(this));
    },
    /**
     * @override
     */
    start: function () {
        this.$el.css({width: '100%'});
        return this._super().then(function () {
            this.trigger_up('edit_mode');
            this.$el.css({width: ''});
        }.bind(this));
    },

    destroy: function () {
        this.trigger_up('readonly_mode');
        this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Asks the user if he really wants to discard its changes (if there are
     * some of them), then simply reload the page if he wants to.
     *
     * @param {boolean} [reload=true]
     *        true if the page has to be reloaded when the user answers yes
     *        (do nothing otherwise but add this to allow class extension)
     * @returns {Deferred}
     */
    cancel: function (reload) {
        var def = $.Deferred();
        if (!this.wysiwyg.isDirty()) {
            def.resolve();
        } else {
            var confirm = Dialog.confirm(this, _t("If you discard the current edition, all unsaved changes will be lost. You can cancel to return to the edition mode."), {
                confirm_callback: def.resolve.bind(def),
            });
            confirm.on('closed', def, def.reject);
        }
        return def.then(function () {
            var $wrapwrap = $('#wrapwrap');
            this.editable($wrapwrap).removeClass('o_editable');
            if (reload !== false) {
                this.wysiwyg.destroy();
                return this._reload();
            } else {
                this.destroy();
            }
        }.bind(this));
    },
    /**
     * Asks the snippets to clean themself, then saves the page, then reloads it
     * if asked to.
     *
     * @param {boolean} [reload=true]
     *        true if the page has to be reloaded after the save
     * @returns {Deferred}
     */
    save: function (reload) {
        this.wysiwyg.save().then(function (dirty) {
            if (dirty && reload !== false) {
                return this._reload();
            } else {
                this.destroy();
            }
        }.bind(this));
    },
    /**
     * Returns the editable areas on the page.
     *
     * @param {DOM} $wrapwrap
     * @returns {jQuery}
     */
    editable: function ($wrapwrap) {
        return $wrapwrap.find('[data-oe-model]')
            .not('.o_not_editable')
            .filter(function () {
                return !$(this).closest('.o_not_editable').length;
            })
            .not('link, script')
            .not('[data-oe-readonly]')
            .not('img[data-oe-field="arch"], br[data-oe-field="arch"], input[data-oe-field="arch"]')
            .not('.oe_snippet_editor')
            .add('.o_editable');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _wysiwygInstance: function () {
        return new WysiwygMultizone(this, {snippetsURL: odoo.snippetsURL});
    },
    /**
     * Reloads the page in non-editable mode, with the right scrolling.
     *
     * @private
     * @returns {Deferred} (never resolved, the page is reloading anyway)
     */
    _reload: function () {
        this.wysiwyg.destroy();
        window.location.hash = 'scrollTop=' + window.document.body.scrollTop;
        if (window.location.search.indexOf(this.LOCATION_SEARCH) >= 0) {
            var regExp = new RegExp('[&?]' + this.LOCATION_SEARCH + '(=[^&]*)?', 'g');
            window.location.href = window.location.href.replace(regExp, '');
        } else {
            window.location.reload(true);
        }
        return $.Deferred();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when the "Discard" button is clicked -> discards the changes.
     *
     * @private
     */
    _onCancelClick: function () {
        this.cancel(false);
    },
    /**
     * Called when the "Save" button is clicked -> saves the changes.
     *
     * @private
     */
    _onSaveClick: function () {
        this.save();
    },
});

return EditorMenu;
});
