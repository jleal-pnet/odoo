odoo.define('mail.inline_activity', function (require) {
"use strict";

var FieldRegistry = require('web.field_registry');
var FormController = require('web.FormController');
var FormView = require('web.FormView');
var WebEditorBackend = require('web_editor.backend');
var HtmlField = WebEditorBackend.FieldTextHtmlSimple;

var InlineActivityFieldTextHtml = HtmlField.extend({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Reduce height of editor for better and smaller UI.
     *
     * @override
     * @private
     */
    _getSummernoteConfig: function () {
        return _.extend(this._super.apply(this, arguments), {
            height: 100,
        });
    }
});

var InlineActivityFormController = FormController.extend({
    className: "o_chat_composer o_activity_inline_form",
    custom_events: _.extend({}, FormController.prototype.custom_events, {
        env_updated: '_onEnvUpdated',
    }),

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Schedule activity and close composer.
     *
     * @override
     * @private
     */
    _onButtonClicked: function (event) {
        var self = this;
        this._super.apply(this, arguments).always(function () {
            self.trigger_up('reload_mail_fields', {activity: true, thread: true});
            self.createRecord();
        });
    },
    /**
     * Stops the propagation of the 'env_updated' event.
     *
     * @private
     */
    _onEnvUpdated: function (ev) {
        ev.stopPropagation();
    },
});

var InlineActivityFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: InlineActivityFormController,
    }),
});

FieldRegistry.add('inline_activity_html', InlineActivityFieldTextHtml);

return {
    InlineActivityFormView: InlineActivityFormView,
    InlineActivityFieldTextHtml: InlineActivityFieldTextHtml
};

});