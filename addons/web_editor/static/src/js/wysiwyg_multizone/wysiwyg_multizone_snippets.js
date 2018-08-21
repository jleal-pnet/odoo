odoo.define('web_editor.wysiwyg.multizone.snippets', function (require) {
'use strict';

var WysiwygMultizone = require('web_editor.wysiwyg.multizone');
var snippetsEditor = require('web_editor.snippet.editor');

/**
 * Can not break a snippet
 */
var WysiwygMultizoneSnippets = WysiwygMultizone.extend({
    events: _.extend({}, WysiwygMultizone.prototype.events, {
        'content_changed .o_editable': '_onChange',
    }),
    custom_events: _.extend({}, WysiwygMultizone.prototype.custom_events, {
        request_history_undo_record: '_onHistoryUndoRecordRequest',
        activate_snippet:  '_onActivateSnippet',
    }),

    /**
     * @override
     */
    start: function () {
        this.snippets = new snippetsEditor.Class(this, this.$editables);
        var def = this.snippets.insertBefore(this._summernote.layoutInfo.editor);
        return $.when(this._super(), def);
    },
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    /*
     * @override
     */
    isUnbreakableNode: function (node) {
        return this._super(node) || $(node).is('div') || snippetsEditor.globalSelector.is($(node));
    },
    /*
     * @override
     */
    save: function () {
        if (!this.isDirty()) {
            return $.when();
        }
        var defs = [];
        this.trigger_up('ready_to_save', {defs: defs});
        return $.when.apply($, defs)
            .then(this.snippets.cleanForSave.bind(this.snippets))
            .then(this._super.bind(this));
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------


    //--------------------------------------------------------------------------
    // Handler
    //--------------------------------------------------------------------------

    /**
     * @override
     * @param {OdooEvent} ev
     * @param {jQuery} ev.data
     */
    _onActivateSnippet: function (ev) {
        if (!$.contains(ev.data[0], this._focusedNode)) {
            this._focusedNode = ev.data[0];
        }
    },
    /**
     * Called when an element askes to record an history undo -> records it.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onHistoryUndoRecordRequest: function (ev) {
        this.addHistoryStep();
    },

    // this._focusedNode
});

return WysiwygMultizoneSnippets;
});
