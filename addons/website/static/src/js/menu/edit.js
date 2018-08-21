odoo.define('website.editMenu', function (require) {
'use strict';

var core = require('web.core');
var weContext = require('web_editor.context');
var EditorMenu = require('website.editor.menu');
var websiteNavbarData = require('website.navbar');

var _t = core._t;

/**
 * Adds the behavior when clicking on the 'edit' button (+ editor interaction)
 */
var EditPageMenu = websiteNavbarData.WebsiteNavbarActionWidget.extend({
    xmlDependencies: ['/website/static/src/xml/website.editor.xml'],
    actions: _.extend({}, websiteNavbarData.WebsiteNavbarActionWidget.prototype.actions, {
        edit: '_startEditMode',
    }),
    custom_events: _.extend({}, websiteNavbarData.WebsiteNavbarActionWidget.custom_events || {}, {
        snippet_dropped: '_onSnippetDropped',
    }),

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this._editorAutoStart = (weContext.getExtra().editable && window.location.search.indexOf('enable_editor') >= 0);
    },
    /**
     * Auto-starts the editor if necessary or add the welcome message otherwise.
     *
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        // Check that the page is empty
        var $wrap = this._targetForEdition().find('#wrap');
        this.$wrap = $wrap;

        if ($wrap.length && $wrap.html().trim() === '') {
            // If readonly empty page, show the welcome message
            this.$welcomeMessage = $(core.qweb.render('website.homepage_editor_welcome_message'));
            this.$welcomeMessage.addClass('o_homepage_editor_welcome_message');
            this.$welcomeMessage.css('min-height', $wrap.parent('main').height() - ($wrap.outerHeight(true) - $wrap.height()));
            $wrap.empty().append(this.$welcomeMessage);
        }


        // If we auto start the editor, do not show a welcome message
        if (this._editorAutoStart) {
            return $.when(def, this._startEditMode());
        }
        return def;
    },

    //--------------------------------------------------------------------------
    // Actions
    //--------------------------------------------------------------------------

    /**
     * Creates an editor instance and appends it to the DOM. Also remove the
     * welcome message if necessary.
     *
     * @private
     * @returns {Deferred}
     */
    _startEditMode: function () {
        var self = this;
        if (this.$welcomeMessage) {
            this.$welcomeMessage.detach(); // detach from the readonly rendering before the clone by summernote
        }
        return new EditorMenu(this).prependTo(document.body).then(function () {
            if (self.$welcomeMessage) {
                self.$wrap.append(self.$welcomeMessage.clone()); // reappend if the user cancel the edition
            }
            var $wrapwrap = self._targetForEdition();
            $wrapwrap.find('.oe_structure.oe_empty, [data-oe-type="html"]').attr('data-editor-message', _t('DRAG BUILDING BLOCKS HERE'));
            var def = $.Deferred();
            self.trigger_up('animation_start_demand', {
                editableMode: true,
                onSuccess: def.resolve.bind(def),
                onFailure: def.reject.bind(def),
            });
            return def;
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _targetForEdition: function () {
        // in edit mode, we have .note-editable className
        return $('#wrapwrap.homepage:not(.note-editable), #wrapwrap.homepage.note-editable');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when a snippet is dropped in the page. Notifies the WebsiteRoot
     * that is should start the animations for this snippet.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onSnippetDropped: function (ev) {
        this.trigger_up('animation_start_demand', {
            editableMode: true,
            $target: ev.data.$target,
        });
    },
});

websiteNavbarData.websiteNavbarRegistry.add(EditPageMenu, '#edit-page-menu');
});
