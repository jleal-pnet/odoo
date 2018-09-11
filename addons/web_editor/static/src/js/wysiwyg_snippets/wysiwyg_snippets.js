odoo.define('web_editor.wysiwyg.snippets', function (require) {
'use strict';

var Wysiwyg = require('web_editor.wysiwyg');
var snippetsEditor = require('web_editor.snippet.editor');

Wysiwyg.include({
    events: _.extend({}, Wysiwyg.prototype.events, {
        'content_changed .o_editable': '_onChange',
    }),
    custom_events: _.extend({}, Wysiwyg.prototype.custom_events, {
        request_history_undo_record: '_onHistoryUndoRecordRequest',
        activate_snippet:  '_onActivateSnippet',
    }),

    init: function (parent, options) {
        this._super.apply(this, arguments);

        options = _.clone(this.options);
        if (!options.snippets) {
            return;
        }
        if (options.snippets === true) {
            options.snippets = 'web_editor.snippets';
        }
        options.isUnbreakableNode = this.isUnbreakableNode.bind(this);
        options.isEditableNode = this.isEditableNode.bind(this);
        this.snippets = new snippetsEditor.Class(this, options);
    },
    /*
     * Preload snippets.
     *
     * @override
     **/
    willStart: function () {
        if (this.snippets) {
            this.snippets.loadSnippets(); // don't use the deferred
        }
        return this._super();
    },
    /**
     * add options (snippets) to load snippet building block
     * snippets can by url begin with '/' or an view xml_id
     *
     * @override
     * @params {string} [options.snippets]
     */
    start: function () {
        var self = this;
        this._super();
        if (!this.snippets) {
            return;
        }
        this.snippets.setEditable(this.$targetDroppable || this.$el.find('.note-editable'));
        this.snippets.insertBefore(this.$el).then(function () {
            self.$el.before(self.snippets.$el);
            setTimeout(function () { // add a set timeout for the transition
                self.snippets.$el.addClass('o_loaded');
                self.$el.addClass('o_snippets_loaded');
            });
        });
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /*
     * @override
     */
    isUnbreakableNode: function (node) {
        if (!this.snippets) {
            return this._super(node);
        }
        return this._super(node) || $(node).is('div') || snippetsEditor.globalSelector.is($(node));
    },
    /*
     * @override
     */
    save: function () {
        if (!this.snippets) {
            return this._super();
        }
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
});

});
