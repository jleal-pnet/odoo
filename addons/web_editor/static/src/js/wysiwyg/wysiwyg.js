odoo.define('web_editor.wysiwyg', function (require) {
'use strict';

var Widget = require('web.Widget');
var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var ServicesMixin = require('web.ServicesMixin');
var mixins = require('web.mixins');
var modulesRegistry = require('web_editor.summernote.plugin.registry');

var QWeb = core.qweb;
var _t = core._t;

/**
TODO:

error: insert video => eject node after video in p => unbreakable
can save in codeview mode

--------------------------------
--------------------------------
Later:

doubleclick image => showImageDialog
key.nameFromCode[27] = 'ESCAPE'; ==> cancel

*/

var Wysiwyg = Widget.extend({
    xmlDependencies: [
        '/web_editor/static/src/xml/wysiwyg.xml',
        '/web_editor/static/src/xml/wysiwyg_colorpicker.xml',
    ],
    /*
     *
     *
     * init options 'recordInfo':
     *   - context
     *   - [res_model]
     *   - [res_id]
     *   - [data_res_model]
     *   - [data_res_id]
     *   @see summernote/widgets.js '_getAttachmentsDomain'
     *
     **/
    init: function (parent, options) {
        this._super.apply(this, arguments);

        this.options = options || {};
        this.attachments = this.options.attachments || [];
        this.hints = [];
        this.$el = null;
        this._dirty = false;
        this.id = _.uniqueId('wysiwyg_');

        var recordInfo = this.options.recordInfo;
        this.options.recordInfo = (function () {
            var data = recordInfo || this._getRecordInfo();
            if (typeof data === 'function') {
                data = data();
            }
            if (!data.context) {
                console.warn('Context is missing');
            }
            data.attachmentIDs = _.pluck(this.attachments, 'id');
            data.user_id = session.uid;
            return data;
        }).bind(this);
    },
    /*
     * Load assets and color picker template then call summernote API
     * and replace $el by the summernote editable node
     *
     * @override
     **/
    willStart: function () {
        this.$target = this.$el;
        this.$el = null; // temporary null to avoid hidden error, setElement when start
        return this._super()
            .then(function () { // load color picker template if needed
                if ('web_editor.colorpicker' in QWeb.templates) {
                    return;
                }
                return this._rpc({
                    model: 'ir.ui.view',
                    method: 'read_template',
                    args: ['web_editor.colorpicker', this.options.recordInfo.context]
                }).then(function (template) {
                    QWeb.add_template(template);
                });
            }.bind(this))
            .then(this._loadInstance.bind(this));
    },
    /**
     * start in sync
     * @override
     */
    start: function () {
        this._value = this._summernote.code();
    },
    /**
     * @override
     */
    destroy: function () {
        // prevents the replacement of the target by the content of summernote
        // (in order to be able to cancel) 
        var removeLayout = $.summernote.ui.removeLayout;
        $.summernote.ui.removeLayout = function ($note, layoutInfo) {
            layoutInfo.editor.remove();
            $note.show();
        };
        this._summernote.destroy();
        $.summernote.ui.removeLayout = removeLayout;
        this.$target.removeAttr('data-wysiwyg-id');
        this.$target.removeData('wysiwyg');
        this._super();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /*
     * undo or redo the editor
     *
     * @param {integer} step
     */
    history: function (step) {
        if (step < 0) {
            while(step) {
                this._summernote.modules.editor.history.rewind();
                step++;
            }
        } else if (step > 0) {
            while(step) {
                this._summernote.modules.editor.history.redo();
                step--;
            }
        }
    },
    /*
     * add a step (undo) in editor
     *
     */
    addHistoryStep: function () {
        var editor = this._summernote.modules.editor;
        editor.createRange();
        editor.history.recordUndo();
    },
    /*
     * save the content in the target
     *
     * @returns {$.Promise} resolve with true if the content was dirty
     */
    save: function () {
        var isDirty = this.isDirty();
        var html = this._summernote.code();
        if (this.$target.is('textarea')) {
            this.$target.val(html);
        } else {
            this.$target.html(html);
        }
        return $.when(isDirty);
    },
    /*
     * returns true if the content has changed
     *
     * @returns {boolean}
     */
    isDirty: function () {
        if (!this._dirty && this._value !== this._summernote.code()) console.warn("not dirty flag ? (eg: font-size)");
        return this._value !== this._summernote.code();
    },
    /*
     * return true if the current node is unbreakable.
     * The text node of unbreakable node, can not be changed, children can
     * not be added or deleted.
     * An unbreakable node can contain nodes that can be edited.
     *
     * @param {DOM} node
     * @returns {Boolean}
     */
    isUnbreakableNode: function (node) {
        return !this.isEditableNode(node) || $.summernote.dom.isMedia(node);
    },
    /*
     * return true if the current node is editable
     *
     * @param {DOM} node
     * @returns {Boolean}
     */
    isEditableNode: function (node) {
        return this.$el.is(node) || $(node).closest(this.$el).length;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @returns {Object} the summernote configuration
     */
    _editorOptions: function () {
        var self = this;
        var allowAttachment = !this.options.noAttachment;

        var options = JSON.parse(JSON.stringify($.summernote.options));

        options.parent = this;
        options.lang = "odoo";
        options.container = this.$target.parent().css('position', 'relative');

        options.focus = false;
        options.disableDragAndDrop = !allowAttachment;
        options.styleTags = ['p', 'pre', 'small', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'];
        options.fontSizes = [_t('Default'), '8', '9', '10', '11', '12', '14', '18', '24', '36', '48', '62'];
        options.minHeight = 180;

        options.keyMap.pc['CTRL+K'] = 'LinkPlugin.show';
        options.keyMap.mac['CMD+K'] = 'LinkPlugin.show';

        options.toolbar = [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['fontsize', ['fontsize']],
            ['color', ['colorpicker']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['table', ['table']],
            ['insert', allowAttachment ? ['linkPlugin', 'mediaPlugin'] : ['linkPlugin']],
            ['history', ['undo', 'redo']],
            ['view', config.debug ? ['fullscreen', 'codeview', 'help'] : ['fullscreen', 'help']]
        ];
        options.popover = {
            image: [
                ['padding'],
                ['imagesize', ['imageSizeAuto', 'imageSize100', 'imageSize50', 'imageSize25']],
                ['float', ['floatLeft', 'floatRight', 'floatNone']],
                ['imageShape'],
                ['cropImage'],
                ['media', ['mediaPlugin', 'removeMedia']],
                ['alt']
            ],
            video: [
                ['padding'],
                ['imagesize', ['imageSize100', 'imageSize50', 'imageSize25']],
                ['float', ['floatLeft', 'floatRight', 'floatNone']],
                ['media', ['mediaPlugin', 'removeMedia']]
            ],
            icon: [
                ['padding'],
                ['faSize'],
                ['float', ['floatLeft', 'floatRight', 'floatNone']],
                ['faSpin'],
                ['media', ['mediaPlugin', 'removeMedia']]
            ],
            document: [
                ['float', ['floatLeft', 'floatRight', 'floatNone']],
                ['media', ['mediaPlugin', 'removeMedia']]
            ],
            link: [
                ['link', ['linkDialogShowPlugin', 'unlink']]
            ],
            table: [
                ['add', ['addRowDown', 'addRowUp', 'addColLeft', 'addColRight']],
                ['delete', ['deleteRow', 'deleteCol', 'deleteTable']]
            ],
        };

        options.hint = {
            match: /\B@(\w+)$/,
            search: function (keyword, callback) {
                self._rpc({
                    model: 'res.partner',
                    method: "search_read",
                    fields: ['id', 'name', 'email'],
                    domain: [['name', 'ilike', keyword]],
                    limit: 10,
                }).then(callback);
            },
            template: function (partner) {
                return partner.name + (partner.email ? ' <i style="color: #999;">(' + partner.email + ')</i>' : '');
            },
            content: function (item) {
                if (!_.findWhere(self.hints, {id: item.id})) {
                    self.hints.push(item);
                }
                return '@' + item.name + String.fromCharCode(160);
            },
        };

        options.callbacks = {
            onChange: this._onChange.bind(this),
            onImageUpload: this._onImageUpload.bind(this),
            onFocusnode: this._onFocusnode.bind(this),
        };

        options.isUnbreakableNode = this.isUnbreakableNode.bind(this);
        options.isEditableNode = this.isEditableNode.bind(this);

        return options;
    },
    /**
     * @private
     * @returns {Object} modules list to load
     */
    _getPlugins: function () {
        return _.extend({}, $.summernote.options.modules, modulesRegistry.map);
    },
    /**
     *  @returns object who describe the linked record
     *      res_id, res_model, xpath
     */
    _getRecordInfo: function () {
        return {};
    },
    /**
     *  create an instance with the API lib
     *
     * @returns {$.Promise}
     */
    _loadInstance: function () {
        var defaultOptions = this._editorOptions();
        var summernoteOptions = _.extend({}, defaultOptions, this.options);

        _.extend(summernoteOptions.callbacks, defaultOptions.callbacks, this.options.callbacks);
        if (this.options.keyMap) {
            _.extend(summernoteOptions.keyMap.pc, defaultOptions.keyMap.pc, this.options.keyMap.pc);
            _.extend(summernoteOptions.keyMap.mac, defaultOptions.keyMap.mac, this.options.keyMap.mac);
        }

        var plugins = _.extend(this._getPlugins(), this.options.plugins);
        summernoteOptions.modules = _.omit(plugins, function (v) {return !v;});

        this.$target.summernote(summernoteOptions);

        this._summernote = this.$target.data('summernote');
        this.$target.attr('data-wysiwyg-id', this.id).data('wysiwyg', this);
        $('.note-editor, .note-popover').not('[data-wysiwyg-id]').attr('data-wysiwyg-id', this.id);

        this.setElement(this._summernote.layoutInfo.editor);

        return $.when();
    },

    //--------------------------------------------------------------------------
    // Handler
    //--------------------------------------------------------------------------

    /**
     * trigger_up 'wysiwyg_change'
     *
     * @private
     */
    _onChange: function () {
        var html = this._summernote.code();
        if (this.hints.length) {
            var hints = [];
            _.each(this.hints, function (hint) {
                if (html.indexOf('@' + hint.name) !== -1) {
                    hints.push(hint);
                }
            });
            this.hints = hints;
        }

        this._dirty = true;
        this.trigger_up('wysiwyg_change', {
            html: html,
            hints: this.hints,
            attachments: this.attachments,
        });
    },
    /**
     * trigger_up 'wysiwyg_attachment' when add an image found in the view.
     *
     * This method is called when an image is uploaded by the media dialog and return the
     * objact attachment from added as record in the "ir.attachment".
     *
     * For e.g. when sending email, this allows people to add attachments with the content
     * editor interface and that they appear in the attachment list.
     * The new documents being attached to the email, they will not be erased by the CRON
     * when closing the wizard.
     *
     * @private
     */
    _onImageUpload: function (attachments) {
        var self = this;
        attachments = _.filter(attachments, function (attachment) {
            return !_.findWhere(self.attachments, {id: attachment.id});
        });
        if (!attachments.length) {
            return;
        }
        this.attachments = this.attachments.concat(attachments);

        // todo remove image not in the view

        this.trigger_up.bind(this, 'wysiwyg_attachment', this.attachments);
    },
    /**
     * Called when the carret focus an other node (focus event, mouse event, or key arrow event)
     * from Unbreakable
     */
    _onFocusnode: function (node) {
        this.trigger_up('wysiwyg_focusnode', {
            node: node,
        });
    },
});

//--------------------------------------------------------------------------
// Public helper
//--------------------------------------------------------------------------

Wysiwyg.createReadyFunction = function (Contructor) {
    var assetsLoaded = false;

    /**
     * Load wysiwyg assets if needed
     *
     * @param {Widget} parent
     * @returns {$.Promise}
    */
    Contructor.ready = function (parent) {
        if (assetsLoaded) {
            return $.when();
        }
        var def = $.Deferred();
        var timeout = setTimeout(function () {
            throw _t("Can't load assets of the wysiwyg editor");
        }, 10000);
        var wysiwyg = new Contructor(parent, {recordInfo: {context: {}}});
        wysiwyg.attachTo($('<textarea>')).then(function () {
            assetsLoaded = true;
            clearTimeout(timeout);
            wysiwyg.destroy();
            def.resolve();
        });
        return def;
    };
};
/**
 * Load wysiwyg assets if needed
 *
 * @see Wysiwyg.createReadyFunction
 * @param {Widget} parent
 * @returns {$.Promise}
*/
Wysiwyg.createReadyFunction(Wysiwyg);
/**
 *
 * @returns {Object}
 * @returns {Node} sc - start container
 * @returns {Number} so - start offset
 * @returns {Node} ec - end container
 * @returns {Number} eo - end offset
*/
Wysiwyg.getRange = function (DOM) {
    var range = $.summernote.range.create();
    return {
        sc: range.sc,
        so: range.so,
        ec: range.ec,
        eo: range.eo,
    };
};
/**
 *
 * @param {Node} sc - start container
 * @param {Number} so - start offset
 * @param {Node} ec - end container
 * @param {Number} eo - end offset
*/
Wysiwyg.setRange = function (sc, so, ec, eo) {
    $(sc).focus();
    if (ec) {
        $.summernote.range.create(sc, so, ec, eo).normalize().select();
    } else {
        $.summernote.range.create(sc, so).normalize().select();
    }
    // trigger for Unbreakable
    $(sc.tagName ? sc : sc.parentNode).trigger('wysiwyg.range');
};
/**
 *
 * @param {Node} node - dom node
 * @param {Object} [options]
 * @param {boolean} options.begin move the range to the beginning of the first node.
 * @param {boolean} options.end move the range to the end of the last node.
*/
Wysiwyg.setRangeFromNode = function (node, options) {
    var last = node;
    while (last.lastChild) { last = last.lastChild; }
    var first = node;
    while (first.firstChild) { first = first.firstChild; }

    if (options && options.begin && !options.end) {
        Wysiwyg.setRange(first, 0);
    } else if (options && !options.begin && options.end) {
        Wysiwyg.setRange(last, last.textContent.length);
    } else {
        Wysiwyg.setRange(first, 0, last, last.textContent.length);
    }
};

return Wysiwyg;
});
