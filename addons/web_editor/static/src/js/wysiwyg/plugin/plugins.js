odoo.define('web_editor.plugins', function (require) {
'use strict';

var AbstractPlugin = require('web_editor.plugin.abstract');
var registry = require('web_editor.plugin.registry');


return _.mapObject($.summernote.options.modules, function (Module, pluginName) {
    var prototype = {
        init: function () {
            this._super.apply(this, arguments);
            this.summernote.options.modules[pluginName].apply(this, arguments);
        },
    };
    _.each(Module.prototype, function (prop, name) {
        if (typeof prop === 'function') {
            prototype[name] = function () {
                return this.summernote.options.modules[pluginName].prototype[name].apply(this, arguments);
            };
        } else {
            prototype[name] = prop;
        }
    });

    var Plugin = AbstractPlugin.extend(prototype);

    // override summernote default buttons
    registry.add(pluginName, Plugin);

    return Plugin;
});

});
