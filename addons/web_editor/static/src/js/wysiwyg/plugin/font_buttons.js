odoo.define('web_editor.plugin.Font.buttons', function (require) {
'use strict';

var Buttons = require('web_editor.plugin.Buttons');

//--------------------------------------------------------------------------
// override the ColorPicker button into the Toolbar and the font size button
//--------------------------------------------------------------------------

Buttons.include({
    addToolbarButtons: function () {
        var self = this;
        this._super();

        var paletteFunction = this.context.memo('button.color');
        this.context.memo('button.colorpicker', function () {
            return self.context.invoke('Font.colorPickerButton', paletteFunction());
        });

        var fontsizeFunction = this.context.memo('button.fontsize');
        this.context.memo('button.fontsize', function () {
            return self.context.invoke('Font.fontSizeButton', fontsizeFunction());
        });
    },
});

});
