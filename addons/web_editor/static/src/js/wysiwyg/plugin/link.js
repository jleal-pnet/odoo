odoo.define('web_editor.summernote.plugin.Link', function (require) {
'use strict';

var core = require('web.core');
var Class = require('web.Class');
var LinkDialog = require('wysiwyg.widgets.LinkDialog');
var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

var _t = core._t;
var dom = $.summernote.dom;
var sLang = $.summernote.lang.odoo;
var sOptions = $.summernote.options;

//--------------------------------------------------------------------------
// link
//--------------------------------------------------------------------------

var SummernoteLinkDialog = sOptions.modules.linkDialog;
var Link = AbstractPlugin.extend(SummernoteLinkDialog.prototype).extend({
    init: function () {
        this._super.apply(this, arguments);
        SummernoteLinkDialog.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public summernote module API
    //--------------------------------------------------------------------------

    /*
     * @override
     */
    showLinkDialog: function (linkInfo) {
        this.context.invoke('imageDialog.hidePopover');

        if (linkInfo.range) {
            var media = this.context.layoutInfo.editable.data('target');
            var r = linkInfo.range.getPoints();

            // move caret in icon, video...
            if (!media && (dom.ancestor(r.sc, dom.isImg) || dom.ancestor(r.sc, dom.isIcon))) {
                media = dom.ancestor(r.sc, dom.isImg) || dom.ancestor(r.sc, dom.isIcon);
            }
            // if select a text content in anchor then click on image then click on anchor button
            if (dom.isImg(media) || dom.isIcon(media)) {
                r.sc = media.parentNode;
                r.so = [].indexOf.call(media.parentNode.childNodes, media);
                r.ec = media;
                r.eo = dom.nodeLength(media);

                linkInfo.range.sc = r.sc;
                linkInfo.range.so = r.so;
                linkInfo.range.ec = r.ec;
                linkInfo.range.eo = r.eo;
            }

            linkInfo.isAnchor = linkInfo.range.isOnAnchor();
            linkInfo.className = linkInfo.isAnchor ? dom.ancestor(r.sc, dom.isAnchor).className : '';
            linkInfo.url = linkInfo.isAnchor ? dom.ancestor(r.sc, dom.isAnchor).href : '';

            var nodes = [];
            if (linkInfo.isAnchor) {
                nodes = dom.ancestor(r.sc, dom.isAnchor).childNodes;
            } else if (!linkInfo.range.isCollapsed()) {
                if (dom.isImg(media) || dom.isIcon(media)) {
                    nodes.push(media);
                } else {
                    if (r.sc.tagName) {
                        r.sc = (r.so ? r.sc.childNodes[r.so] : r.sc).firstChild || r.sc;
                        r.so = 0;
                    } else if (r.so !== r.sc.textContent.length) {
                        if (r.sc === r.ec) {
                            r.ec = r.sc = r.sc.splitText(r.so);
                            r.eo -= r.so;
                        } else {
                            r.sc = r.sc.splitText(r.so);
                        }
                        r.so = 0;
                    }
                    if (r.ec.tagName) {
                        r.ec = (r.eo ? r.ec.childNodes[r.eo-1] : r.ec).lastChild || r.ec;
                        r.eo = r.ec.textContent.length;
                    } else if (r.eo !== r.ec.textContent.length) {
                        r.ec.splitText(r.eo);
                    }

                    // browsers can't target a picture or void node
                    if (dom.isVoid(r.sc) || dom.isImg(r.sc)) {
                        r.so = dom.listPrev(r.sc).length-1;
                        r.sc = r.sc.parentNode;
                    }
                    if (dom.isBR(r.ec)) {
                        r.eo = dom.listPrev(r.ec).length-1;
                        r.ec = r.ec.parentNode;
                    } else if (dom.isVoid(r.ec) || dom.isImg(r.sc)) {
                        r.eo = dom.listPrev(r.ec).length;
                        r.ec = r.ec.parentNode;
                    }
                    linkInfo.range.sc = r.sc;
                    linkInfo.range.so = r.so;
                    linkInfo.range.ec = r.ec;
                    linkInfo.range.eo = r.eo;
                    linkInfo.range.select();
                    this.context.invoke('editor.saveRange');
                    linkInfo.range = this.context.invoke('editor.createRange');

                    // search nodes to insert in the anchor

                    var startPoint = {
                        node: r.sc,
                        offset: r.so
                    };
                    var endPoint = {
                        node: r.ec,
                        offset: r.eo
                    };
                    dom.walkPoint(startPoint, endPoint, function (point) {
                        var node = point.node.childNodes && point.node.childNodes[point.offset] || point.node;
                        nodes.push(node);
                    });

                    nodes = _.filter(_.uniq(nodes), function (node) {
                        return nodes.indexOf(node.parentNode) === -1;
                    });
                }
            }

            if (nodes.length > 0) {
                var text = "";
                linkInfo.images = [];
                for (var i=0; i<nodes.length; i++) {
                    if (dom.ancestor(nodes[i], dom.isImg)) {
                        text += dom.ancestor(nodes[i], dom.isImg).outerHTML;
                    } else if (dom.ancestor(nodes[i], dom.isIcon)) {
                        text += dom.ancestor(nodes[i], dom.isIcon).outerHTML;
                    } else if (!linkInfo.isAnchor && nodes[i].nodeType === 1) {
                        // just use text nodes from listBetween
                    } else if (!linkInfo.isAnchor && i===0) {
                        text += nodes[i].textContent;
                    } else if (!linkInfo.isAnchor && i===nodes.length-1) {
                        text += nodes[i].textContent;
                    } else {
                        text += nodes[i].textContent;
                    }
                }
                linkInfo.text = text.replace(/[ \t\r\n]+/g, ' ');
            }

            linkInfo.needLabel = !linkInfo.text.length;
        }

        var range = linkInfo.range;
        var def = $.Deferred();
        var linkDialog = new LinkDialog(this.options.parent,
            this.context.invoke('imageDialog.getWidgetOptions'),
            _.omit(linkInfo, 'range')
        );

        linkDialog.on('save', this, function (newLinkInfo) {
            linkInfo.range.select();
            this.context.invoke('editor.saveRange');
            def.resolve(newLinkInfo);
            var range = this.context.invoke('editor.createRange');
            var anchor = dom.ancestor(range.sc, dom.isAnchor);
            $(anchor).attr('class', newLinkInfo.className);
        });
        linkDialog.on('closed', this, function () {
            def.reject();
        });

        linkDialog.open();
        return def.promise();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _addButtons: function () {
        var self = this;
        this._super();

        this.context.memo('help.LinkPlugin.show', this.options.langInfo.help['linkDialog.show']);

        this.context.memo('button.linkPlugin', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.link),
                tooltip: self.lang.link.link + self.context.invoke('buttons.representShortcut', 'LinkPlugin.show'),
                click: self.context.createInvokeHandler('LinkPlugin.show')
            }).render();
        });

        this.context.memo('button.linkDialogShowPlugin', function () {
            return self.context.invoke('buttons.button', {
                contents: self.ui.icon(self.options.icons.link),
                tooltip: self.lang.link.edit,
                click: self.context.createInvokeHandler('LinkPlugin.show')
            }).render();
        });
    },

});

// override summernote default dialog
registry.add('LinkPlugin', Link);

return Link;

});