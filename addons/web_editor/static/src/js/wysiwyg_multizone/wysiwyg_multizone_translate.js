odoo.define('web_editor.wysiwyg.multizone.translate', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('wysiwyg.widgets.Dialog');
var WysiwygMultizone = require('web_editor.wysiwyg.multizone');
var Wysiwyg = require('web_editor.wysiwyg');

var _t = core._t;


var AttributeTranslateDialog = Dialog.extend({
    /**
     * @constructor
     */
    init: function (parent, options, node) {
        this._super(parent, _.extend({
            title: _t("Translate Attribute"),
            buttons: [
                {text:  _t("Close"), classes: 'btn-primary', click: this.save}
            ],
        }, options || {}));
        this.translation = $(node).data('translation');
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var $group = $('<div/>', {class: 'form-group'}).appendTo(this.$el);
        _.each(this.translation, function (node, attr) {
            var $node = $(node);
            var $label = $('<label class="col-form-label"></label>').text(attr);
            var $input = $('<input class="form-control"/>').val($node.html());
            $input.on('change keyup', function () {
                var value = $input.val();
                $node.html(value).trigger('change', node);
                $node.data('$node').attr($node.data('attribute'), value).trigger('translate');
                $node.trigger('change');
            });
            $group.append($label).append($input);
        });
        return this._super.apply(this, arguments);
    }
});

var WysiwygTranslate = WysiwygMultizone.extend({
    /**
     *
     * @override
     * @param {string} options.lang
     */
    init: function (parent, options) {
        this.lang = options.lang;
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        this._super();

        var $translations = $();
        var attrs = ['placeholder', 'title', 'alt'];
        _.each(attrs, function (attr) {
            self.$editables.filter('['+attr+'*="data-oe-translation-id="]').filter(':empty, input, select, textarea, img').each(function () {
                var $node = $(this);
                var translation = $node.data('translation') || {};
                var trans = $node.attr(attr);
                var match = trans.match(/<span [^>]*data-oe-translation-id="([0-9]+)"[^>]*>(.*)<\/span>/);
                var $trans = $(trans).addClass('d-none o_editable o_editable_translatable_attribute').appendTo('body');
                $trans.data('$node', $node).data('attribute', attr);

                translation[attr] = $trans[0];
                $node.attr(attr, match[2]);

                var select2 = $node.data('select2');
                if (select2) {
                    select2.blur();
                    $node.on('translate', function () {
                        select2.blur();
                    });
                    $node = select2.container.find('input');
                }
                $node.addClass('o_translatable_attribute').data('translation', translation);
            });
        });

        this.translations = [];
        this.$editables_attr = this.$editables.filter('.o_translatable_attribute');
        this.$editables_attribute = $('.o_editable_translatable_attribute');

        this.$editables_attribute.on('change', this._onChange.bind(this));

        this._markTranslatableNodes();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /*
     *
     * @override
     */
    save: function () {
        this.$editables = this.$editables.add(this.$editables_attribute);
        return this._super();
    },
    /*
     * @override
     */
    isDirty: function () {
        return this._super() || this.$editables_attribute.hasClass('o_dirty');
    },
    /*
     * @override
     */
    isUnbreakableNode: function (node) {
        return this._super(node) || $(node).data('oe-readonly');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getRecordInfo: function (editable) {
        var recordInfo = this._super(editable);
        recordInfo.context.lang = this.lang;
        recordInfo.translation_id = $(editable).data('oe-translation-id')|0;
        return recordInfo;
    },
    /**
     * @override
     */
    _saveElement: function (outerHTML, recordInfo, editable) {
        if (!recordInfo.translation_id) {
            return this._super(outerHTML, recordInfo);
        }
        return this._rpc({
            model: 'ir.translation',
            method: 'save_html',
            args: [
                [recordInfo.translation_id],
                $(editable).html(),
                recordInfo.context
            ],
        }).fail(function (error) {
           Dialog.alert(null, error.data.message);
       });
    },
    /**
     * @override
     */
    _editorOptions: function () {
        var self = this;
        var options = this._super();
        options.toolbar = [
            // todo: hide this feature for field (data-oe-model)
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['fontsize', ['fontsize']],
            ['color', ['color']],
            // keep every time
            ['history', ['undo', 'redo']],
        ];
        return options;
    },
    /**
     * @override
     */
    _getPlugins: function () {
        var plugins = this._super();
        return _.omit(plugins, 'linkPopover', 'ImagePopover', 'MediaPlugin', 'ImagePlugin', 'VideoPlugin', 'IconPlugin', 'DocumentPlugin', 'tablePopover');
    },
    /**
     * Called when text is edited -> make sure text is not messed up and mark
     * the element as dirty.
     *
     * @override
     * @param {Jquery Event} [ev]
     */
    _onChange: function (ev) {
        var $node = $(ev && ev.target || this._getFocusedEditable());
        if (!$node.length) {
            return;
        }
        $node.find('p').each(function () { // remove <p/> element which might have been inserted because of copy-paste
            var $p = $(this);
            $p.after($p.html()).remove();
        });
        var trans = this._getTranlationObject($node[0]);
        $node.toggleClass('o_dirty', trans.value !== $node.html().replace(/[ \t\n\r]+/, ' '));
    },
    /**
     * @private
     */
    _getTranlationObject: function (node) {
        var $node = $(node);
        var id = +$node.data('oe-translation-id');
        if (!id) {
            id = $node.data('oe-model')+','+$node.data('oe-id')+','+$node.data('oe-field');
        }
        var trans = _.find(this.translations, function (trans) {
            return trans.id === id;
        });
        if (!trans) {
            this.translations.push(trans = {'id': id});
        }
        return trans;
    },
    /**
     * @private
     */
    _markTranslatableNodes: function () {
        var self = this;
        this.$editables.add(this.$editables_attribute).each(function () {
            var $node = $(this);
            var trans = self._getTranlationObject(this);
            trans.value = (trans.value ? trans.value : $node.html() ).replace(/[ \t\n\r]+/, ' ');
        });
        this.$editables.parent().prependEvent('click.translator', function (ev) {
            if (ev.ctrlKey || !$(ev.target).is(':o_editable')) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
        });

        // attributes

        this.$editables_attr.each(function () {
            var $node = $(this);
            var translation = $node.data('translation');
            _.each(translation, function (node, attr) {
                var trans = self._getTranlationObject(node);
                trans.value = (trans.value ? trans.value : $node.html() ).replace(/[ \t\n\r]+/, ' ');
                $node.attr('data-oe-translation-state', (trans.state || 'to_translate'));
            });
        });

        this.$editables_attr.prependEvent('mousedown.translator click.translator mouseup.translator', function (ev) {
            if (ev.ctrlKey) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            if (ev.type !== 'mousedown') {
                return;
            }

            new AttributeTranslateDialog(self, {}, ev.target).open();
        });
    },
});

return WysiwygTranslate;
});
