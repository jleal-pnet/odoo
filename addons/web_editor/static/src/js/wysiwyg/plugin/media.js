odoo.define('web_editor.plugin.media', function (require) {
'use strict';

var core = require('web.core');
var weWidgets = require('wysiwyg.widgets');
var AbstractPlugin = require('web_editor.plugin.abstract');
var registry = require('web_editor.plugin.registry');

var _t = core._t;

var dom = $.summernote.dom;
var sOptions = $.summernote.options;
var ui = $.summernote.ui;
var range = $.summernote.range;
var sLang = $.summernote.lang.odoo;

//--------------------------------------------------------------------------
// Media (for image, video, icon, document)
//--------------------------------------------------------------------------

dom.isMedia = function (node) {
    return dom.isImg(node) ||
        dom.isIcon(node) ||
        dom.isDocument(node) ||
        dom.isVideo(node);
};

var MediaPlugin = AbstractPlugin.extend({
    events: {
        'summernote.mousedown': '_onMouseDown',
        'summernote.keyup': '_onKeyup',
        'summernote.scroll': '_onScroll',
        'summernote.disable': '_onDisable',
        'summernote.change': '_onChange',
        'summernote.codeview.toggled': '_onChange',
    },
    initialize: function () {
        var self = this;
        this._super.apply(this, arguments);
        setTimeout(function () {
            $('a.o_image:empty, span.fa:empty', self.editable).text(' '); // Required for editing (delete, backspace) with summernote
        });
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    showImageDialog: function () {
        var self = this;

        this.context.invoke('editor.saveRange');
        var media = this.context.invoke('editor.restoreTarget');

        var mediaDialog = new weWidgets.MediaDialog(this.options.parent,
            this.options.recordInfo(),
            $(media).clone()[0]
        );

        mediaDialog.on('saved', this, function (data) {
            this.insertMedia(media, data);
        });
        mediaDialog.on('closed', this, function () {
            this.context.invoke('editor.restoreRange');
        });

        mediaDialog.open();
    },
    removeMedia: function () {
        var $target = $(this.restoreTarget()).parent();
        this.context.triggerEvent('media.delete', $target, this.$editable);
        debugger
    },
    update: function (target) {
        if (!target) {
            target = this.context.invoke('editor.restoreTarget');
        }

        this.hidePopovers();

        if (this.context.isDisabled()) {
            return;
        }
        if (!target) {
            return;
        }

        if (!dom.isMedia(target)) {
            this.context.invoke('editor.clearTarget');
            return;
        }

        this.context.triggerEvent('focusnode', target);
        this.context.invoke('editor.saveTarget', target);

        var range = this.context.invoke('editor.createRange');
        var prev = dom.prevPointUntil({node: target, offset: 0}, function (point) {
            return dom.isVisiblePoint(point) && dom.isText(point.node);
        });
        range.sc = range.ec = prev.node;
        range.so = range.eo = prev.offset;

        range.normalize().select();
        this.context.invoke('editor.saveRange');

        if (dom.isImg(target)) {
            this.context.invoke('ImagePlugin.show', target);
        } else if (dom.isIcon(target)) {
            this.context.invoke('IconPlugin.show', target);
        } else if (dom.isVideo(target)) {
            this.context.invoke('VideoPlugin.show', target);
        } else if (dom.isDocument(target)) {
            this.context.invoke('DocumentPlugin.show', target);
        }
    },
    /*
     * Warning, hide popover remove the saved target
     */
    hidePopovers: function () {
        this.context.invoke('handle.hide');
        this.context.invoke('ImagePlugin.hide');
        this.context.invoke('IconPlugin.hide');
        this.context.invoke('VideoPlugin.hide');
        this.context.invoke('DocumentPlugin.hide');
    },
    insertMedia: function (previous, data) {
        var deferred = $.Deferred();
        var newMedia = data.media;
        this._wrapCommand(function () {
            if (newMedia.tagName !== "IMG") {
                $(newMedia).filter('a.o_image:empty, span.fa:empty').text(" "); // Required for editing (delete, backspace) with summernote
                deferred.resolve();
            } else {
                $(newMedia).one('load error abort', deferred.resolve.bind(deferred));
            }
            range.create(this.editable).insertNode(newMedia);
        })();

        deferred.then(function () {
            // select new media
            window.event = { // because summernote use global 'event' for position ; Todo, create not jquery event
                pageX: $(newMedia).offset().left,
                pageY: $(newMedia).offset().top,
            };
            $(newMedia).trigger('mousedown').trigger('mouseup');
        });

        return deferred.promise();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _addButtons: function () {
        var self = this;
        this._super();

        this.context.memo('button.mediaPlugin', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.picture),
                tooltip: self.lang.image.image,
                click: self.context.createInvokeHandler('MediaPlugin.showImageDialog')
            }).render();
        });

        this.context.memo('button.removeMedia', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.trash),
                tooltip: self.lang.image.remove,
                click: self._wrapCommand(function () {
                    this.context.invoke('MediaPlugin.removeMedia');
                })
            }).render();
        });

        var padding = [null, 'padding-small', 'padding-medium', 'padding-large', 'padding-xl'];
        var values = _.zip(padding, this.lang.image.paddingList);
        this._createDropdownButton('padding', this.options.icons.padding, this.lang.image.padding, values);
    },

    //--------------------------------------------------------------------------
    // handle
    //--------------------------------------------------------------------------

    /*
     * @param {SummernoteEvent} se
     * @param {jQueryEvent} se
     */
    _onKeyup: function (se, e) {
        return this.update(e.target);
    },
    _onScroll: function (se, e) {
        return this.update(e.target);
    },
    _onChange: function (se, e) {
        return this.update(e.target);
    },
    _onMouseDown: function (se, e) {
        if (this.update(e.target)) {
            e.preventDefault();
        }
    },
    _onDisable: function () {
        this.hidePopovers();
    }
});

//--------------------------------------------------------------------------
// Abstract
//--------------------------------------------------------------------------

var AbstractMediaPlugin = AbstractPlugin.extend({
    targetType: null,
    initialize: function () {
        this._super.apply(this, arguments);
        this.$popover = this.ui.popover({className: 'note-' + this.targetType + '-popover'})
            .render().appendTo(this.options.container);
        var $content = this.$popover.find('.popover-content, .note-popover-content');
        this.context.invoke('buttons.build', $content, this.options.popover[this.targetType]);
    },
    destroy: function () {
        this.$popover.remove();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    hide: function () {
        this.$popover.hide();
    },
    show: function (target) {
        this._popoverPosition(target);
        ui.toggleBtnActive(this.$popover.find('a, button'), false);
        var $target = $(target);

        var float = $target.css('float');
        var floatIcon = this.options.icons[_.str.camelize('align_' + (float !== 'none' ? float : 'justify'))];
        ui.toggleBtnActive(this.$popover.find('.note-float button:has(.' + floatIcon + ')'), true);

        var padding = (($target.attr('class') || '').match(/(^| )(padding-[^\s]+)( |$)/) || ['fa-1x'])[2];
        ui.toggleBtnActive(this.$popover.find('.note-padding a:has(li[data-value="' + padding + '"])'), true);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _popoverPosition: function (target) {
        var pos = $(target).offset();
        var posContainer = this.context.layoutInfo.editor.parent().offset();
        pos.top -= posContainer.top;
        pos.left -= posContainer.left;
        this.$popover.css({
            display: 'block',
            left: event.pageX - posContainer.left - 20,
            top: event.pageY - posContainer.top,
        });
    },
    _isMedia: function (target) {},
});

//--------------------------------------------------------------------------
// Image
//--------------------------------------------------------------------------

var ImagePlugin = AbstractMediaPlugin.extend({
    targetType: 'image',

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    cropImageDialog: function () {
        this.context.invoke('editor.saveRange');

        var media = this.context.invoke('editor.restoreTarget');
        var cropImageDialog = new weWidgets.CropImageDialog(this.options.parent,
            this.options.recordInfo(),
            $(media).clone()
        );
        cropImageDialog.on('saved', this, function (data) {
            this.context.invoke('MediaPlugin.insertMedia', media, data);
        });
        cropImageDialog.on('closed', this, function () {
            this.context.invoke('editor.restoreRange');
        });

        cropImageDialog.open();
    },
    altDialg: function () {
        this.context.invoke('editor.saveRange');

        var media = this.context.invoke('editor.restoreTarget');
        var altDialog = new weWidgets.AltDialog(this.options.parent,
            this.options.recordInfo(),
            $(media).clone()
        );
        altDialog.on('saved', this, this._wrapCommand(function (data) {
            $(media).attr('alt', $(data.media).attr('alt'))
                    .attr('title', $(data.media).attr('title'));
        }));
        altDialog.on('closed', this, function () {
            this.context.invoke('editor.restoreRange');
        });

        altDialog.open();
    },
    show: function (target) {
        this._super(target);
        var $target = $(target);

        this.context.invoke('handle.update', target);

        var iconShape = this.options.icons.imageShape;
        _.each(this.options.icons.imageShape, function (icon, className) {
            ui.toggleBtnActive(this.$popover.find('.note-imageShape button:has(.' + icon.replace(/\s+/g, '.') + ')'), $target.hasClass(className));
        }.bind(this));

        var size = (($target.attr('style') || '').match(/width:\s*([0-9]+)%/i) || [])[1];
        ui.toggleBtnActive(this.$popover.find('.note-imagesize button:contains(' + (size ? size + '%' : this.lang.image.imageSizeAuto) + ')'), true);

        ui.toggleBtnActive(this.$popover.find('.note-cropImage button'), $target.hasClass('o_cropped_img_to_save'));
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

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
    _addButtons: function () {
        var self = this;
        this._super();
        // add all shape buttons if this option is active
        this.context.memo('button.imageShape', function () {
            var $el = $();
            _.each(['rounded', 'rounded-circle', 'shadow', 'img-thumbnail'], function (shape) {
                $el = $el.add(self._createToggleButton(null, self.options.icons.imageShape[shape], self.lang.image.imageShape[shape], shape));
            });
            return $el;
        });
        this.context.memo('button.cropImage', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.cropImage),
                tooltip: self.lang.image.cropImage,
                click: self.context.createInvokeHandler('ImagePlugin.cropImageDialog')
            }).render();
        });
        this.context.memo('button.alt', function () {
            return self.context.invoke('buttons.button', {
                contents: '<b>' + self.lang.image.alt + '</b>',
                click: self.context.createInvokeHandler('ImagePlugin.altDialg')
            }).render();
        });
        this.context.memo('button.imageSizeAuto', function () {
            return self.context.invoke('buttons.button', {
                contents: '<span class="note-iconsize-10">' + self.lang.image.imageSizeAuto + '</span>',
                click: self._wrapCommand(function () {
                    var target = this.context.invoke('editor.restoreTarget');
                    $(target).css({
                        width: '',
                        height: ''
                    });
                })
            }).render();
        });
    },
    _isMedia: function (target) {
        return dom.isImg(target);
    },
});

_.extend(sOptions.icons, {
    padding: 'fa fa-plus-square-o',
    cropImage: 'fa fa-crop',
    imageShape: {
        rounded: 'fa fa-square',
        'rounded-circle': 'fa fa-circle-o',
        shadow: 'fa fa-sun-o',
        'img-thumbnail': 'fa fa-picture-o',
    },
});
_.extend(sLang.image, {
    padding: _t('Padding'),
    paddingList: [_t('None'), _t('Small'), _t('Medium'), _t('Large'), _t('Xl')],
    imageSizeAuto: _t('Auto'),
    cropImage: _t('Crop image'),
    imageShape: {
        rounded: _t('Shape: Rounded'),
        'rounded-circle': _t('Shape: Circle'),
        shadow: _t('Shape: Shadow'),
        'img-thumbnail': _t('Shape: Thumbnail'),
    },
    alt: _t('Description:'),
});

//--------------------------------------------------------------------------
// Video
//--------------------------------------------------------------------------

dom.isVideo = function (node) {
    return node.tagName === "DIV" && (node.className.indexOf('css_editable_mode_display') !== -1 || node.className.indexOf('media_iframe_video') !== -1);
};

var VideoPlugin = AbstractMediaPlugin.extend({
    targetType: 'video',
    /*
     * @override
     */
    show: function (target) {
        if (target.tagName === "DIV" && target.className.indexOf('css_editable_mode_display') !== -1) {
            target = target.parentNode;
            this.context.invoke('editor.saveTarget', target);
        }
        return this._super(target);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _isMedia: function (target) {
        return dom.isVideo(target);
    },
});

//--------------------------------------------------------------------------
// Icons: Icon Awsome (and other with themes)
//--------------------------------------------------------------------------

dom.isIcon = function (node) {
    return node && (node.tagName === "SPAN" && node.className.indexOf(' fa-') !== -1);
};

var IconPlugin = AbstractMediaPlugin.extend({
    targetType: 'icon',
    /*
     * @override
     */
    show: function (target) {
        this._super(target);

        var $target = $(target);
        ui.toggleBtnActive(this.$popover.find('.note-faSpin button'), $target.hasClass('fa-spin'));
        var faSize = (($target.attr('style') || '').match(/font-size:\s*([0-9](em|px))(;|$)/) || [])[1];
        if (!faSize) {
            faSize = (($target.attr('class') || '').match(/(^| )fa-([0-9])x( |$)/) || [])[2] + 'em';
        }
        ui.toggleBtnActive(this.$popover.find('.note-faSize a:has(li[data-value="' + faSize + '"])'), true);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _popoverPosition: function (target) {
        var size = parseInt($(target).css('font-size'));
        var pos = $(target).offset();
        var posContainer = this.context.layoutInfo.editor.parent().offset();
        pos.top -= posContainer.top;
        pos.left -= posContainer.left;
        this.$popover.css({
            display: 'block',
            left: pos.left + size - 5,
            top: pos.top - 5
        });
    },
    _isMedia: function (target) {
        return dom.isIcon(target);
    },
    _addButtons: function () {
        var self = this;
        this._super();
        var values = [['1em', '1x'], ['2em', '2x'], ['3em', '3x'], ['4em', '4x'], ['5em', '5x']];
        this._createDropdownButton('faSize', this.options.icons.faSize, this.lang.image.faSize, values, function (ev) {
            $(self.context.invoke('editor.restoreTarget')).css('font-size', $(ev.target).data('value'));
        });
        this._createToggleButton('faSpin', this.options.icons.faSpin, this.lang.image.faSpin, 'fa-spin');
    },
});
_.extend(sOptions.icons, {
    faSize: 'fa fa-expand',
    faSpin: 'fa fa-refresh',
});
_.extend(sLang.image, {
    faSize: _t('Icon size'),
    faSpin: _t('Spin'),
});

//--------------------------------------------------------------------------
// Media Document
//--------------------------------------------------------------------------

dom.isDocument = function (node) {
    return node && (node.tagName === "A" && node.className.indexOf('o_image') !== -1);
};

var DocumentPlugin = AbstractMediaPlugin.extend({
    targetType: 'document',

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /*
     * @override
     */
    _popoverPosition: function (target) {
        var pos = $(target).offset();
        var posContainer = this.context.layoutInfo.editor.parent().offset();
        pos.top -= posContainer.top;
        pos.left -= posContainer.left;
        this.$popover.css({
            display: 'block',
            left: pos.left + $(target).width() - 15,
            top: pos.top - 15
        });
    },
    _isMedia: function (target) {
        return dom.isDocument(target);
    },
});

registry.add('MediaPlugin', MediaPlugin)
    .add('ImagePlugin', ImagePlugin)
    .add('VideoPlugin', VideoPlugin)
    .add('IconPlugin', IconPlugin)
    .add('DocumentPlugin', DocumentPlugin);

// modules to remove from summernote
registry.add('imagePopover', null);

return {
    MediaPlugin: MediaPlugin,
    ImagePlugin: ImagePlugin,
    VideoPlugin: VideoPlugin,
    IconPlugin: IconPlugin,
    DocumentPlugin: DocumentPlugin,
};

});