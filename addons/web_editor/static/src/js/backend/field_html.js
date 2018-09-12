odoo.define('web_editor.field.html', function (require) {
'use strict';

var basic_fields = require('web.basic_fields');
var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var Wysiwyg = require('web_editor.wysiwyg');
var field_registry = require('web.field_registry');

var TranslatableFieldMixin = basic_fields.TranslatableFieldMixin;

var QWeb = core.qweb;
var _t = core._t;


console.error("todo: this.nodeOptions['style-inline']");

console.error('todo: readonly in iframe');
// mass_mailing: /mass_mailing/static/src/css/basic_theme_readonly.css

console.error('insert js mass_mailing');
/*

mass_mailing/static/src/js/mass_mailing_editor.js
mass_mailing.FieldTextHtmlInline

To remove: 

FieldTextHtmlInline
FieldTextHtmlPopupContent

*/

/**
 * FieldHtml Widget
 * Intended to display HTML content. This widget uses the wysiwyg editor
 * improved by odoo.
 *
 * nodeOptions:
 *  - no-attachment
 *  - cssEdit
 *  - cssReadonly
 *  - snippets
 *  - wrapper
 *
 */
var FieldHtml = basic_fields.DebouncedField.extend(TranslatableFieldMixin, {
    className: 'oe_form_field oe_form_field_html_text',
    supportedFieldTypes: ['html'],

    custom_events: {
        wysiwyg_change: '_doDebouncedAction',
        wysiwyg_attachment: '_onAttachmentChange',
    },

    willStart: function () {
        var defAsset = this.nodeOptions.cssReadonly && ajax.loadAsset(this.nodeOptions.cssReadonly);
        return $.when(this._super().then(Wysiwyg.ready.bind(null, this)), defAsset);
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
        if (this.wysiwyg.isDirty()) {
            this._isDirty = true;
        }
        return this.wysiwyg.save().then(this._super.bind(this));
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
        return this.$target.val();
    },
    /**
     * create the wysiwyg instance with the target
     * add the editable content: this.$content
     *
     * @private
     * @returns {$.Promise}
     */
    _createWysiwygIntance: function () {
        this.wysiwyg = new Wysiwyg(this, this._getWysiwygOptions());

        // by default it's synchronus because the assets are already loaded in willStart
        // but can be async with option like iframe, snippets...
        return this.wysiwyg.attachTo(this.$target).then(function () {
            this.$content = this.wysiwyg.$el;
            this._onWysiwygIntance();
        }.bind(this));
    },
    /**
     * get wysiwyg options to create wysiwyg instance
     *
     * @private
     * @returns {Object}
     */
    _getWysiwygOptions: function () {
        return {
            recordInfo: {
                context: this.record.getContext(this.recordParams),
                res_model: this.model,
                res_id: this.res_id,
            },
            noAttachment: this.nodeOptions['no-attachment'],
            inIframe: !!this.nodeOptions.cssEdit,
            iframeCssAssets: this.nodeOptions.cssEdit,
            snippets: this.nodeOptions.snippets,
        };
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
        this.$target = $('<textarea>').val(this._textToHtml(this.value)).hide();
        this.$target.appendTo(this.$el);

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

        if (this.nodeOptions.cssEdit) {
            // must be async because the target must be append in the DOM
            setTimeout(this._createWysiwygIntance.bind(this));
        } else {
            return this._createWysiwygIntance();
        }
    },
    /**
     * @override
     * @private
     */
    _renderReadonly: function () {
        var value = this._textToHtml(this.value);
        if (this.nodeOptions.wrapper) {
            value = this._wrap(value);
        }

        this.$el.empty();

        if (this.nodeOptions.cssReadonly) {
            this.$iframe = $('<iframe class="o_readonly"/>');
            this.$iframe.appendTo(this.$el);

            // inject content in iframe

            this.$iframe.one('load', function onLoad () {
                ajax.loadAsset(this.nodeOptions.cssReadonly).then(function (asset) {
                    var cwindow = this.$iframe[0].contentWindow;
                    cwindow.document
                        .open("text/html", "replace")
                        .write(
                            '<head>' +
                                '<meta charset="utf-8">' +
                                '<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">\n' +
                                '<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">\n' +
                                _.map(asset.cssLibs, function (cssLib) {
                                    return '<link type="text/css" rel="stylesheet" href="' + cssLib + '"/>';
                                }).join('\n') + '\n' +
                                _.map(asset.cssContents, function (cssContent) {
                                    return '<style type="text/css">' + cssContent + '</style>';
                                }).join('\n') + '\n' +
                            '</head>\n' +
                            '<body class="o_in_iframe o_readonly">\n' +
                                '<div id="iframe_target">' + value + '</div>\n' +
                            '</body>');
                    this._resize();
                }.bind(this));
            }.bind(this));
        } else {
            this.$content = $('<div class="o_readonly"/>').html(value);
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
    _onWysiwygIntance: function () {
        this.$el.closest('.note.editor').find('.note-toolbar').append(this._renderTranslateButton());
    },
    _wrap: function (html) {
        return $(QWeb.render(this.nodeOptions.wrapper))
            .find('#wrapper').html(html)
            .end().prop('outerHTML');
    },
    _unWrap: function (html) {
        return $(html).find('#wrapper').html();
    },
});


field_registry.add('html', FieldHtml);


return FieldHtml;
});
