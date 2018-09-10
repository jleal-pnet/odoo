odoo.define('web_editor.wysiwyg.multizone', function (require) {
'use strict';
var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var mixins = require('web.mixins');
var ServicesMixin = require('web.ServicesMixin');
var weContext = require('web_editor.context');
var Wysiwyg = require('web_editor.wysiwyg');

var QWeb = core.qweb;
var _t = core._t;


/**
 * jQuery extensions
 */
$.extend($.expr[':'], {
    o_editable: function (node, i, m) {
        while (node) {
            if (node.className && _.isString(node.className)) {
                if (node.className.indexOf('o_not_editable')!==-1 ) {
                    return false;
                }
                if (node.className.indexOf('o_editable')!==-1 ) {
                    return true;
                }
            }
            node = node.parentNode;
        }
        return false;
    },
});

$.fn.extend({
    focusIn: function () {
        if (this.length) {
            Wysiwyg.setRangeFromNode(this[0], {begin: true});
            $(this).trigger('mouseup');
        }
        return this;
    },
    focusInEnd: function () {
        if (this.length) {
            Wysiwyg.setRangeFromNode(this[0], {end: true});
            $(this).trigger('mouseup');
        }
        return this;
    },
    selectContent: function () {
        if (this.length) {
            Wysiwyg.setRangeFromNode(this[0]);
            $(this).trigger('mouseup');
        }
        return this;
    },
});


/**
 * HtmlEditor
 * Intended to edit HTML content. This widget uses the Wysiwyg editor
 * improved by odoo.
 *
 * class editable: o_editable
 * class non editable: o_not_editable
 *
 */
var WysiwygMultizone = Wysiwyg.extend({
    events: {
        'keyup *': function (event) {
            if ((event.keyCode === 8 || event.keyCode === 46)) {
                var $target = $(event.target).closest('.o_editable');
                if (!$target.is(':has(*:not(p):not(br))') && !$target.text().match(/\S/)) {
                    $target.empty();
                }
            }
        },
        'click .note-editable': function (ev) {
            ev.preventDefault();
        },
        'submit .note-editable form .btn': function (ev) {
            ev.preventDefault(); // Disable form submition in editable mode
        },
        'hide.bs.dropdown .dropdown': function (ev) {
            // Prevent dropdown closing when a contenteditable children is focused
            if (ev.originalEvent
                    && $(ev.target).has(ev.originalEvent.target).length
                    && $(ev.originalEvent.target).is('[contenteditable]')) {
                ev.preventDefault();
            }
        },
    },
    /**
     * Use 'attachTo'
     *
     * @override
     *
     * @param {Object} options.context - the context to use for the saving rpc
     * @param {boolean} [options.withLang=false]
     *        false if the lang must be omitted in the context (saving "master"
     *        page element)
     */
    init: function (parent, options) {
        this._super(this, options);
        this.setParent(parent);
        this.savingMutex = new concurrency.Mutex();
    },
    /**
     * Prevent some default features for the editable area.
     *
     * @private
     */
    start: function () {
        var self = this;
        this._super();
        // Unload preserve
        var flag = false;
        window.onbeforeunload = function (event) {
            if (self.isDirty() && !flag) {
                flag = true;
                _.defer(function () { flag=false; });
                return _t('This document is not saved!');
            }
        };
        // firefox & IE fix
        try {
            document.execCommand('enableObjectResizing', false, false);
            document.execCommand('enableInlineTableEditing', false, false);
            document.execCommand('2D-position', false, false);
        } catch (e) { /* */ }
        document.body.addEventListener('resizestart', function (evt) {evt.preventDefault(); return false;});
        document.body.addEventListener('movestart', function (evt) {evt.preventDefault(); return false;});
        document.body.addEventListener('dragstart', function (evt) {evt.preventDefault(); return false;});
        // BOOTSTRAP preserve
        this.init_bootstrap_carousel = $.fn.carousel;
        $.fn.carousel = function () {
            var res = self.init_bootstrap_carousel.apply(this, arguments);
            // off bootstrap keydown event to remove event.preventDefault()
            // and allow to change cursor position
            $(this).off('keydown.bs.carousel');
            return res;
        };
        this.$('.dropdown-toggle').dropdown();
        this.$el
            .tooltip({
                selector: '[data-oe-readonly]',
                container: 'body',
                trigger: 'hover',
                delay: { 'show': 1000, 'hide': 100 },
                placement: 'bottom',
                title: _t("Readonly field")
            })
            .on('click', function () {
                $(this).tooltip('hide');
            });
        $('body').addClass('editor_enable');
        $('.note-editor, .note-popover').filter('[data-wysiwyg-id="' + this.id + '"]').addClass('wysiwyg_frontend');
    },
    /**
     * @override
     */
    destroy: function () {
        this._super();
        this.$target.attr('id', this.$target.attr('data-id')).css('display', '');
        this.$target.removeAttr('data-id');
        $('body').removeClass('editor_enable');
        window.onbeforeunload = null;
        $.fn.carousel = this.init_bootstrap_carousel;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /*
     *
     * @override
     * @returns {$.Promise} resolve with true if the content was dirty
     */
    save: function () {
        if (!this.isDirty()) {
            return $.when(false);
        }
        this.savingMutex.exec(this._saveCroppedImages.bind(this));
        this.$editables.filter('.o_dirty').each(function (index, editable) {
            this.savingMutex.exec(this._saveEditable.bind(this, editable));
        }.bind(this));
        return this.savingMutex.def
            .then(this._super.bind(this))
            .then(function () {return true;});
    },
    isDirty: function () {
        return this.$editables.filter('.o_dirty').length;
    },
    /*
     * @override
     */
    isUnbreakableNode: function (node) {
        return this._super(node) || !$(node).is(':o_editable');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _editorOptions: function () {
        var self = this;
        var options = this._super();
        options.toolbar[8] = ['view', ['help']];
        options.popover.image[4] = ['editImage', ['cropImage', 'transform']];
        return _.extend(options, {
            styleWithSpan: false,
            followingToolbar: false,
        });
    },
    /**
     * @private
     */
    _saveEditable: function (editable) {
        var self = this;
        var recordInfo = this._getRecordInfo(editable);
        var outerHTML = this._getCleanedHtml(editable).prop('outerHTML');
        var def = this._saveElement(outerHTML, recordInfo, editable);
        def.done(function () {
            self.trigger_up('saved', recordInfo);
        }).fail(function () {
            self.trigger_up('canceled', recordInfo);
        });
        return def;
    },
    /**
     * @private
     * @returns {Promise}
     */
    _saveCroppedImages: function () {
        var self = this;
        var defs = this.$editables.find('.o_cropped_img_to_save').map(function (croppedImg) {
            var $croppedImg = $(croppedImg);
            $croppedImg.removeClass('o_cropped_img_to_save');
            var resModel = $croppedImg.data('crop:resModel');
            var resID = $croppedImg.data('crop:resID');
            var cropID = $croppedImg.data('crop:id');
            var mimetype = $croppedImg.data('crop:mimetype');
            var originalSrc = $croppedImg.data('crop:originalSrc');
            var datas = $croppedImg.attr('src').split(',')[1];
            if (!cropID) {
                var name = originalSrc + '.crop';
                return self._rpc({
                    model: 'ir.attachment',
                    method: 'create',
                    args: [{
                        res_model: resModel,
                        res_id: resID,
                        name: name,
                        datas_fname: name,
                        datas: datas,
                        mimetype: mimetype,
                        url: originalSrc, // To save the original image that was cropped
                    }],
                }).then(function (attachmentID) {
                    return self._rpc({
                        model: 'ir.attachment',
                        method: 'generate_access_token',
                        args: [[attachmentID]],
                    }).then(function (access_token) {
                        $croppedImg.attr('src', '/web/image/' + attachmentID + '?access_token=' + access_token[0]);
                    });
                });
            } else {
                return self._rpc({
                    model: 'ir.attachment',
                    method: 'write',
                    args: [[cropID], {datas: datas}],
                });
            }
        }).get();
        return $.when.apply($, defs);
    },
    /**
     * Saves one (dirty) element of the page.
     *
     * @private
     * @param {string} outerHTML
     * @param {Object} recordInfo
     * @param {DOM} editable
     * @returns {Promise}
     */
    _saveElement: function (outerHTML, recordInfo, editable) {
        return this._rpc({
            model: 'ir.ui.view',
            method: 'save',
            args: [
                recordInfo.res_id,
                outerHTML,
                recordInfo.xpath,
                recordInfo.context,
            ],
        });
    },
    /**
     * Internal text nodes escaped for XML storage.
     *
     * @private
     * @param {jQuery} $el
     */
    _escapedElements: function ($el) {
        var toEscape = $el.find('*').addBack();
        toEscape = toEscape.not(toEscape.filter('object,iframe,script,style,[data-oe-model][data-oe-model!="ir.ui.view"]').find('*').addBack());
        toEscape.contents().each(function () {
            if (this.nodeType === 3) {
                this.nodeValue = $('<div />').text(this.nodeValue).html();
            }
        });
    },
    /**
     * Gets jQuery cloned element with clean for XML storage
     *
     * @private
     * @param {jQuery} $el
     * @return {jQuery}
     */
    _getCleanedHtml: function (editable) {
        var $el = $(editable).clone().removeClass('o_editable o_dirty');
        this._escapedElements($el);
        return $el;
    },
    /**
     * @override
     * @returns object who describe the linked record
     *      res_id, res_model, xpath
     */
    _getRecordInfo: function (editable) {
        if (!editable) {
            editable = this._getFocusedEditable();
        }
        var $editable = $(editable);
        return {
            res_id: $editable.data('oe-id'),
            res_model: $editable.data('oe-model'),
            xpath: $editable.data('oe-xpath'),
            context: weContext.get(),
        };
    },
    /**
     * @private
     */
    _getFocusedEditable: function () {
        return $(this._focusedNode).closest(this.$editables)[0];
    },
    /**
     * @override
     */
    _loadInstance: function () {
        var $target = this.$target;
        var id = $target.attr('id');
        var className = $target.attr('class');
        $target.off('.WysiwygFrontend');
        $target.attr('data-id', id).removeAttr('id');
        return this._super().then(function () {
            this.$el.attr('id', id).addClass(className);
            this.$editables = this.$('.o_editable');
        }.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handler
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _onChange: function () {
        this._super.apply(this, arguments);
        var editable = this._getFocusedEditable();
        $(editable).addClass('o_dirty');
    },
    /**
     * @override
     */
    _onFocusnode: function (node) {
        this._super.apply(this, arguments);
        this._focusedNode = node;
    },
});

//--------------------------------------------------------------------------
// Public helper
//--------------------------------------------------------------------------

/**
 * Load wysiwyg assets if needed
 *
 * @see Wysiwyg.createReadyFunction
 * @param {Widget} parent
 * @returns {$.Promise}
*/
Wysiwyg.createReadyFunction(WysiwygMultizone);

return WysiwygMultizone;
});