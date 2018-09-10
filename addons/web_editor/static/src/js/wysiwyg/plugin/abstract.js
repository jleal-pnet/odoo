odoo.define('web_editor.summernote.plugin.abstract', function (require) {
'use strict';

var Class = require('web.Class');

//--------------------------------------------------------------------------
// AbstractPlugin for summernote module API
//--------------------------------------------------------------------------

var AbstractPlugin = Class.extend({
    /*
     * Use this prop if you want to extend a summernote plugin
     *.
    _extendSummernotePluginName: null,
    /*
    events: {
        'summernote.mousedown': '_onMouseDown',
        'summernote.mouseup': '_onMouseUp',
        'summernote.keyup': '_onKeyup',
        'summernote.keydown': '_onKeydown',
        'summernote.scroll': '_onScroll',
        'summernote.disable': '_onDisable',
        'summernote.change': '_onChange',
        'summernote.codeview.toggled': '_onChange',
    },
    */
    init: function (context) {
        var self = this;
        this.context = context;
        this.$editable = context.layoutInfo.editable;
        this.editable = this.$editable[0];
        this.window = this.editable.ownerDocument.defaultView;
        this.summernote = this.window._summernoteSlave || $.summernote; // if the target is in iframe
        this.ui = this.summernote.ui;
        this.$editingArea = context.layoutInfo.editingArea;
        this.options = context.options;
        this.lang = this.options.langInfo;
        this._addButtons();
        if (this.events) {
            this.events = _.clone(this.events);
            _.each(_.keys(this.events), function (key) {
                var value = self.events[key];
                if (typeof value === 'string') {
                    if (self[value]) {
                        self.events[key] = self[value].bind(self);
                    } else {
                        delete self.events[key];
                    }
                }
            });
        }
    },

    //--------------------------------------------------------------------------
    // Public summernote module API
    //--------------------------------------------------------------------------

    destroy: function () {},
    shouldInitialize: function () { return true; },
    initialize: function () {},

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _addButtons: function () {
    },
    _createDropdownButton: function (optionName, buttonIcon, buttonTooltip, values, onclick) {
        var self = this;

        if (!onclick) {
            onclick = function (e) {
                var classNames = _.map(values, function (item) { return item[0]; }).join(' ');
                var $target = $(self.context.invoke('editor.restoreTarget'));
                $target.removeClass(classNames);
                if ($(e.target).data('value')) {
                    $target.addClass($(e.target).data('value'));
                }
            };
        }

        function render () {
            return self.ui.buttonGroup([
                self.context.invoke('buttons.button', {
                    className: 'dropdown-toggle',
                    contents: buttonIcon.indexOf('<') === -1 ?
                        self.ui.dropdownButtonContents(self.ui.icon(buttonIcon), self.options) :
                        buttonIcon,
                    tooltip: buttonTooltip,
                    data: {
                        toggle: 'dropdown'
                    }
                }),
                self.ui.dropdown({
                    items: values,
                    template: function (item) {
                        return '<li ' + (item[0] ? 'data-value="' + item[0] + '"' : '') + '>' + item[1] + '</li>';
                    },
                    click: self._wrapCommand(onclick),
                })
            ]).render();
        }
        if (optionName) {
            this.context.memo('button.' + optionName, render);
        } else {
            return render();
        }
    },
    _createToggleButton: function (optionName, buttonIcon, buttonTooltip, className) {
        var self = this;
        return this._createButton(optionName, buttonIcon, buttonTooltip, function () {
            var $target = $(self.context.invoke('editor.restoreTarget'));
            $target.toggleClass(className);
        });
    },
    _createButton: function (optionName, buttonIcon, buttonTooltip, onclick) {
        var self = this;
        function render () {
            return self.context.invoke('buttons.button', {
                contents: buttonIcon.indexOf('<') === -1 ? self.ui.icon(buttonIcon) : buttonIcon,
                tooltip: buttonTooltip,
                click: self._wrapCommand(onclick),
            }).render();
        }
        if (optionName) {
            this.context.memo('button.' + optionName, render);
        } else {
            return render();
        }
    },
    _wrapCommand: function (fn) {
        return function () {
            this.context.invoke('editor.restoreRange');
            this.context.invoke('editor.beforeCommand');
            fn.apply(this, arguments);
            this.context.invoke('editor.saveRange');
            this.context.invoke('editor.afterCommand');
            this.$editable.trigger('change');
        }.bind(this);
    },
});

return AbstractPlugin;

});
