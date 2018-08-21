odoo.define('web_editor.field.html', function (require) {
'use strict';

var basic_fields = require('web.basic_fields');
var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var Wysiwyg = require('web_editor.wysiwyg');
var transcoder = require('web_editor.transcoder');

var TranslatableFieldMixin = basic_fields.TranslatableFieldMixin;

var QWeb = core.qweb;
var _t = core._t;


/**
 * FieldTextHtmlSimple Widget
 * Intended to display HTML content. This widget uses the wysiwyg editor
 * improved by odoo.
 *
 */
var FieldTextHtmlSimple = basic_fields.DebouncedField.extend(TranslatableFieldMixin, {
    className: 'oe_form_field oe_form_field_html_text',
    supportedFieldTypes: ['html'],

    custom_events: {
        wysiwyg_change: '_doDebouncedAction',
        wysiwyg_attachment: '_onAttachmentChange',
    },

    willStart: function () {
        return this._super().then(Wysiwyg.ready.bind(null, this));
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Wysiwyg doesn't notify for changes done in code mode. We override
     * commitChanges to manually switch back to normal mode before committing
     * changes, so that the widget is aware of the changes done in code mode.
     *
     * @override
     */
    commitChanges: function () {
        if (this._getValue() !== this.value) {
            this._isDirty = true;
        }
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    isSet: function () {
        return this.value && this.value !== "<p><br/></p>" && this.value.match(/\S/);
    },
    /**
     * @override
     */
    getFocusableElement: function () {
        return this.$content || this._super.apply(this, arguments);
    },
    /**
     * Do not re-render this field if it was the origin of the onchange call.
     *
     * @override
     */
    reset: function (record, event) {
        this._reset(record, event);
        if (!event || event.target !== this) {
            if (this.mode === 'edit') {
                this.$content.html(this._textToHtml(this.value));
            } else {
                this._renderReadonly();
            }
        }
        return $.when();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _getValue: function () {
        if (this.nodeOptions['style-inline']) {
            transcoder.attachmentThumbnailToLinkImg(this.$content);
            transcoder.fontToImg(this.$content);
            transcoder.classToStyle(this.$content);
        }
        return this.$content.html();
    },
    /**
     * trigger_up 'field_changed' add record into the "ir.attachment" field found in the view.
     * This method is called when an image is uploaded by the media dialog.
     *
     * For e.g. when sending email, this allows people to add attachments with the content
     * editor interface and that they appear in the attachment list.
     * The new documents being attached to the email, they will not be erased by the CRON
     * when closing the wizard.
     *
     * @private
     */
    _onAttachmentChange: function (attachments) {
        if (!this.fieldNameAttachment) {
            return;
        }
        this.trigger_up('field_changed', {
            dataPointID: this.dataPointID,
            changes: _.object([this.fieldNameAttachment], [{
                operation: 'ADD_M2M',
                ids: attachments
            }])
        });
    },
    /**
     * @override
     * @private
     */
    _renderEdit: function () {
        this.$textarea = $('<textarea>').val(this._textToHtml(this.value));
        // his.$textarea.html(this._textToHtml(this.value)); to test
        this.$textarea.appendTo(this.$el);

        var fieldNameAttachment =_.chain(this.recordData)
            .pairs()
            .find(function (value) {
                return _.isObject(value[1]) && value[1].model === "ir.attachment";
            })
            .first()
            .value();
        if (fieldNameAttachment) {
            this.fieldNameAttachment = fieldNameAttachment;
        }

        this.wysiwyg = new Wysiwyg(this, {
            recordInfo: {
                context: this.record.getContext(this.recordParams),
                res_model: this.model,
                res_id: this.res_id,
            },
            'no-attachment': this.nodeOptions['no-attachment'],
        });

        // it's synchronus because the assets are already loaded in willStart
        this.wysiwyg.attachTo(this.$textarea);

        this.$content = this.wysiwyg.$el;
        // this.$content.html(this._textToHtml(this.value));
        // trigger a mouseup to refresh the editor toolbar
        this.$content.trigger('mouseup');
        if (this.nodeOptions['style-inline']) {
            transcoder.styleToClass(this.$content);
            transcoder.imgToFont(this.$content);
            transcoder.linkImgToAttachmentThumbnail(this.$content);
        }
        this.$('.note-toolbar').append(this._renderTranslateButton());
    },
    /**
     * @override
     * @private
     */
    _renderReadonly: function () {
        var self = this;
        this.$el.empty();
        if (this.nodeOptions['style-inline']) {
            var $iframe = $('<iframe class="o_readonly"/>');
            $iframe.on('load', function () {
                self.$content = $($iframe.contents()[0]).find("body");
                self.$content.html(self._textToHtml(self.value));
                self._resize();
            });
            $iframe.appendTo(this.$el);
        } else {
            this.$content = $('<div class="o_readonly"/>');
            this.$content.html(this._textToHtml(this.value));
            this.$content.appendTo(this.$el);
        }
    },
    /**
     * Sets the height of the iframe.
     *
     * @private
     */
    _resize: function () {
        var height = this.$content[0] ? this.$content[0].scrollHeight : 0;
        this.$('iframe').css('height', Math.max(30, Math.min(height, 500)) + 'px');
    },
    /**
     * @private
     * @param {string} text
     * @returns {string} the text converted to html
     */
    _textToHtml: function (text) {
        var value = text || "";
        try {
            $(text)[0].innerHTML; // crashes if text isn't html
        } catch (e) {
            if (value.match(/^\s*$/)) {
                value = '<p><br/></p>';
            } else {
                value = "<p>" + value.split(/<br\/?>/).join("<br/></p><p>") + "</p>";
                value = value
                            .replace(/<p><\/p>/g, '')
                            .replace('<p><p>', '<p>')
                            .replace('<p><p ', '<p ')
                            .replace('</p></p>', '</p>');
            }
        }
        return value;
    },
    /**
     * @override
     * @private
     * @returns {jQueryElement}
     */
    _renderTranslateButton: function () {
        if (_t.database.multi_lang && this.field.translate && this.res_id) {
            return $(QWeb.render('web_editor.FieldTextHtml.button.translate', {widget: this}))
                .on('click', this._onTranslate.bind(this));
        }
        return $();
    },

});

return FieldTextHtmlSimple;
});
