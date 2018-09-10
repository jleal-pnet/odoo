odoo.define('web_editor.wysiwyg.iframe', function (require) {
'use strict';

var Wysiwyg = require('web_editor.wysiwyg');


var _fnSummernoteMaster = $.fn.summernote;
$.fn.summernote = function () {
    var summernote = this[0].ownerDocument.defaultView._fnSummenoteSlave || _fnSummernoteMaster;
    return summernote.apply(this, arguments);
};

Wysiwyg.include({

    init: function (parent, options) {
        this._super.apply(this, arguments);
        if (this.options.inIframe) {
            this._wysiwygIframeCssAssets = this.options._wysiwygIframeCssAssets || 'web_editor.wysiwyg_iframe_css_assets';
            this._onUpdateIframeSummernoteId = 'onLoad_'+ this.subLib;
        }
    },
    /*
     * Load assets to inject in iframe
     *
     * @override
     **/
    willStart: function () {
        if (!this.options.inIframe) {
            return this._super();
        }
        var rpcDef;
        if (this._wysiwygIframeCssAssets && !Wysiwyg._iframeCssAssetsCache[this._wysiwygIframeCssAssets]) {
            rpcDef = this._rpc({
                model: 'ir.qweb',
                method: 'render',
                args: [this._wysiwygIframeCssAssets, {}, this.options.recordInfo().context]
            }).then(function (html) {
                var $assets = $(html).filter('link');

                var assets = 
                    '<meta charset="utf-8">'+
                    '<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">\n'+
                    '<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">\n'+
                    $assets.map(function () {return this.outerHTML;}).get().join('\n');

                Wysiwyg._iframeCssAssetsCache[this._wysiwygIframeCssAssets] = assets;
            }.bind(this));
        }

        return rpcDef
            .then(this._loadIframe.bind(this))
            .then(this._super.bind(this)).then(function () {
                var _summernoteMaster = $.summernote;
                var _summernoteSlave = this.$iframe[0].contentWindow._summernoteSlave;
                _summernoteSlave.options = _.extend({}, _summernoteMaster.options, {modules: _summernoteSlave.options.modules});
                this._enableBootstrapInIframe();
            }.bind(this));
    },
    destroy: function () {
        if (!this.options.inIframe) {
            return this._super();
        }
        $(document.body).off('.' + this.id);

        this.$target.insertBefore(this.$iframe);

        delete window.top[this._onUpdateIframeSummernoteId];
        if (this.$iframeTarget) {
            this.$iframeTarget.remove();
        }
        if (this.$iframe) {
            this.$iframe.remove();
        }
        this._super();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _enableBootstrapInIframe: function () {
        var body =this.$iframe[0].contentWindow.document.body;
        var $toolbarButtons = this._summernote.layoutInfo.toolbar.find('[data-toggle="dropdown"]').dropdown({boundary: body});
        function hideDrowpdown (ev) {
            var $expended = $toolbarButtons.filter('[aria-expanded="true"]').parent();
            $expended.children().removeAttr('aria-expanded').removeClass('show');
            $expended.removeClass('show');
        }
        $(body).on('mouseup.' + this.id, hideDrowpdown);
        $(document.body).on('click.' + this.id, hideDrowpdown);
    },
    /**
     * create iframe, inject css and create a link with the content
     * then inject the target inside
     */
    _loadIframe: function () {
        var $target = this.$el;
        if (!document.body.contains($target[0])) {
            console.error('Target must be present in the DOM');
        }

        this.$iframe = $('<iframe>').css({
            'min-height': '400px',
            width: '100%'
        });
        this.$iframe.insertAfter($target);
        var loadDef = $.Deferred();
        this.$iframe.on('load', loadDef.resolve.bind(loadDef));

        // resolve deferred on load

        var def = $.Deferred();
        window.top[this._onUpdateIframeSummernoteId] = function () {
            delete window.top[this._onUpdateIframeSummernoteId];
            this.$iframe.contents().find('#wysiwyg_target').append($target);
            def.resolve();
        }.bind(this);

        // inject content in iframe

        loadDef.then(function () {
                // inject HTML
            var cwindow = this.$iframe[0].contentWindow;
            cwindow.document
                .open("text/html", "replace")
                .write('<head>' + Wysiwyg._iframeCssAssetsCache[this._wysiwygIframeCssAssets] + '</head>'+
                    '<body>'+
                        '<div id="wysiwyg_target"></div>'+
                        '<script type="text/javascript">'+
                            'window.$ = window.jQuery = window.top.jQuery;'+
                            'var _summernoteMaster = $.summernote;'+
                            'var _fnSummernoteMaster = $.fn.summernote;'+
                            'delete $.summernote;'+
                            'delete $.fn.summernote;'+
                        '</script>\n'+
                        '<script type="text/javascript" src="/web_editor/static/lib/summernote/summernote.js"></script>\n'+
                        '<script type="text/javascript">'+
                            '_summernoteSlave = $.summernote;'+
                            '_summernoteSlave.iframe = true;'+
                            '_summernoteSlave.lang = _summernoteMaster.lang;'+
                            '_fnSummenoteSlave = $.fn.summernote;'+
                            '$.summernote = _summernoteMaster;'+
                            '$.fn.summernote = _fnSummernoteMaster;'+
                            'window.top.' + this._onUpdateIframeSummernoteId + '()'+
                        '</script>\n'+
                    '</body>');
        }.bind(this));

        return def.promise();
    },
});

//--------------------------------------------------------------------------
// Public helper
//--------------------------------------------------------------------------

/**
 *
 * @returns {Object}
 * @returns {Node} sc - start container
 * @returns {Number} so - start offset
 * @returns {Node} ec - end container
 * @returns {Number} eo - end offset
*/
Wysiwyg.getRange = function (DOM) {
    var summernote = DOM.ownerDocument.defaultView._fnSummenoteSlave || _fnSummernoteMaster;
    var range = summernote.range.create();
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
    var summernote = DOM.ownerDocument.defaultView._fnSummenoteSlave || _fnSummernoteMaster;
    $(sc).focus();
    if (ec) {
        summernote.range.create(sc, so, ec, eo).normalize().select();
    } else {
        summernote.range.create(sc, so).normalize().select();
    }
    // trigger for Unbreakable
    $(sc.tagName ? sc : sc.parentNode).trigger('wysiwyg.range');
};


Wysiwyg._iframeCssAssetsCache = {};
});
