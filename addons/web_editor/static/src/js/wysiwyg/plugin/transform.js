odoo.define('web_editor.summernote.plugin.transform', function (require) {
'use strict';

var core = require('web.core');
var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

var _t = core._t;

var sOptions = $.summernote.options;
var sLang = $.summernote.lang.odoo;

//--------------------------------------------------------------------------
// unbreakable node preventing editing
//--------------------------------------------------------------------------

var TransformPlugin = AbstractPlugin.extend({
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    transform: function () {
        var $image = $(this.context.invoke('editor.restoreTarget'));

        if ($image.data('transfo-destroy')) {
            $image.removeData('transfo-destroy');
            return;
        }

        $image.transfo();

        var mouseup = function (event) {
            $('.note-popover button[data-event="transform"]').toggleClass('active', $image.is('[style*="transform"]'));
        };
        $(document).on('mouseup', mouseup);

        var mousedown = this._wrapCommand(function (event) {
            if (!$(event.target).closest('.transfo-container').length) {
                $image.transfo('destroy');
                $(document).off('mousedown', mousedown).off('mouseup', mouseup);
            }
            if ($(event.target).closest('.note-popover').length) {
                $image.data('transfo-destroy', true).attr('style', ($image.attr('style') || '').replace(/[^;]*transform[\w:]*;?/g, ''));
            }
        });
        $(document).on('mousedown', mousedown);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _addButtons: function () {
        var self = this;
        this._super();

        this.context.memo('button.transform', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.transform),
                tooltip: self.lang.image.transform,
                click: self.context.createInvokeHandler('TransformPlugin.transform')
            }).render();
        });
    },

    //--------------------------------------------------------------------------
    // Handler
    //--------------------------------------------------------------------------


});


_.extend(sOptions.icons, {
    transform: 'fa fa-object-ungroup',
});
_.extend(sLang.image, {
    transform: _t('Transform the picture (click twice to reset transformation)'),
});

registry.add('TransformPlugin', TransformPlugin);

return TransformPlugin;

});
