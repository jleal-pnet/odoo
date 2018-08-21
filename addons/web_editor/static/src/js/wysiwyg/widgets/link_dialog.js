odoo.define('wysiwyg.widgets.LinkDialog', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('wysiwyg.widgets.Dialog');

var _t = core._t;

/**
 * Allows to customize link content and style.
 */
var LinkDialog = Dialog.extend({
    template: 'wysiwyg.widgets.link',
    xmlDependencies: Dialog.prototype.xmlDependencies.concat(
        ['/web_editor/static/src/xml/editor.xml']
    ),
    events: _.extend({}, Dialog.prototype.events || {}, {
        'input': '_onAnyChange',
        'change': '_onAnyChange',
        'input input[name="url"]': '_onURLInput',
    }),

    /**
     * @constructor
     */
    init: function (parent, options, linkInfo) {
        this._super(parent, _.extend({
            title: _t("Link to"),
        }, options || {}));

        var dom = $.summernote.dom;

        this.data = linkInfo || {};
        this.data.className = "";
        this.needLabel = linkInfo.needLabel;
        this.data.iniClassName = linkInfo.className;
        this.data.className = linkInfo.iniClassName.replace(/(^|\s+)btn(-[a-z0-9_-]*)?/gi, ' ');
    },
    /**
     * @override
     */
    start: function () {
        var self = this;

        this.$('input.link-style').prop('checked', false).first().prop('checked', true);
        if (this.data.iniClassName) {
            _.each(this.$('input.link-style, select.link-style > option'), function (el) {
                var $option = $(el);
                if ($option.val() && self.data.iniClassName.indexOf($option.val()) >= 0) {
                    if ($option.is("input")) {
                        $option.prop("checked", true);
                    } else {
                        $option.parent().val($option.val());
                    }
                }
            });
        }
        if (this.data.url) {
            var match = /mailto:(.+)/.exec(this.data.url);
            this.$('input[name="url"]').val(match ? match[1] : this.data.url);
        }

        // Hide the duplicate color buttons (most of the times, primary = alpha
        // and secondary = beta for example but this may depend on the theme)
        this.opened().then(function () {
            var colors = [];
            _.each(self.$('.o_btn_preview'), function (btn) {
                var $btn = $(btn);
                var color = $btn.css('background-color');
                if (_.contains(colors, color)) {
                    $btn.remove();
                } else {
                    colors.push(color);
                }
            });
        });

        this._adaptPreview();

        this.$('input:visible:first').focus();

        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    save: function () {
        var data = this._getData();
        if (data === null) {
            var $url = this.$('input[name="url"]');
            $url.closest('.form-group').addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid');
            $url.focus();
            return $.Deferred().reject();
        }
        this.data.text = data.label;
        this.data.url = data.url;
        this.data.className = data.classes.replace(/\s+/gi, ' ').replace(/^\s+|\s+$/gi, '');
        if (data.classes.replace(/(^|[ ])(btn-secondary|btn-success|btn-primary|btn-info|btn-warning|btn-danger)([ ]|$)/gi, ' ')) {
            this.data.style = {'background-color': '', 'color': ''};
        }
        this.data.isNewWindow = data.isNewWindow;
        this.final_data = this.data;
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _adaptPreview: function () {
        var $preview = this.$("#link-preview");
        var data = this._getData();
        if (data === null) {
            return;
        }
        $preview.attr({
            target: data.isNewWindow ? '_blank' : '',
            href: data.url && data.url.length ? data.url : '#',
            class: data.classes.replace(/pull-\w+/, '') + ' o_btn_preview',
        }).html((data.label && data.label.length) ? data.label : data.url);
    },
    /**
     * @private
     */
    _getData: function () {
        var $url = this.$('input[name="url"]');
        var url = $url.val();
        var label = this.$('input[name="label"]').val() || url;

        if (label && this.data.images) {
            for (var i = 0 ; i < this.data.images.length ; i++) {
                label = label.replace(/</, "&lt;").replace(/>/, "&gt;").replace(/\[IMG\]/, this.data.images[i].outerHTML);
            }
        }

        if ($url.prop('required') && (!url || !$url[0].checkValidity())) {
            return null;
        }

        var style = this.$('input[name="link_style_color"]:checked').val() || '';
        var shape = this.$('select[name="link_style_shape"]').val() || '';
        var size = this.$('select[name="link_style_size"]').val() || '';
        var shapes = shape.split(',');
        var outline = shapes[0] === 'outline';
        shape = shapes.slice(outline ? 1 : 0).join(' ');
        var classes = (this.data.className || '')
            + (style ? (' btn btn-' + (outline ? 'outline-' : '') + style) : '')
            + (shape ? (' ' + shape) : '')
            + (size ? (' btn-' + size) : '');
        var isNewWindow = this.$('input[name="is_new_window"]').prop('checked');

        if (url.indexOf('@') >= 0 && url.indexOf('mailto:') < 0 && !url.match(/^http[s]?/i)) {
            url = ('mailto:' + url);
        }
        return {
            label: label,
            url: url,
            classes: classes,
            isNewWindow: isNewWindow,
        };
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onAnyChange: function () {
        this._adaptPreview();
    },
    /**
     * @private
     */
    _onURLInput: function (ev) {
        $(ev.currentTarget).closest('.form-group').removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');
        var isLink = $(ev.currentTarget).val().indexOf('@') < 0;
        this.$('input[name="is_new_window"]').closest('.form-group').toggleClass('d-none', !isLink);
    },
});

return LinkDialog;
});
