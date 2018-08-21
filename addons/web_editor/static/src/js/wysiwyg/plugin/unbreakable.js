odoo.define('web_editor.summernote.plugin.unbreakable', function (require) {
'use strict';

var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

var dom = $.summernote.dom;

//--------------------------------------------------------------------------
// unbreakable node preventing editing
//--------------------------------------------------------------------------

var Unbreakable = AbstractPlugin.extend({
    events: {
        'wysiwyg.range': '_onRange',
        'summernote.mouseup': '_onMouseUp',
        'summernote.keyup': '_onKeyup',
        'summernote.keydown': '_onKeydown',
        // 'summernote.focusnode': '_onFocusnode', => add this event to summernote.
    },
    init: function (context) {
        var self = this;
        this._super(context);
        var isUnbreakableNode = context.options.isUnbreakableNode;
        this.isUnbreakableNode = function (node) {
            node = node.tagName ? node : node.parentNode;
            if (!node) {
                return true;
            }
            return isUnbreakableNode(node);
        };
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /*
     * trigger an focusnode event when the focus enter in an other node
     *
     * @param {DOM} se
     */
    _focusNode: function (node) {
        if (!node.tagName) {
            node = node.parentNode;
        }
        if (this._focusedNode !== node) {
            this._focusedNode = node;
            this.context.triggerEvent('focusnode', node);
        }
    },
    /*
     * change the selection if it's break an unbreakable node
     *
        <unbreakable id="a">
            content_1
            <unbreakable id="b">content_2</unbreakable>
            <allow id="c">
                content_3
                <unbreakable id="d">content_4</unbreakable>
                <unbreakable id="e">
                    content_5
                    <allow id="f">content_6</allow>
                    content_7
                </unbreakable>
                content_8
            </allow>
            <unbreakable id="f">content_9</unbreakable>
            <allow id="g">
                content_10
                <unbreakable id="h">content_11</unbreakable>
                content_12
            </allow>
        </p>

        START            END            RESIZE START     RESIZE END

        content_1       content_1       content_3       content_3   (find the first allowed node)
        content_1       content_2       content_3       content_3
        content_1       content_3       content_3       -
        content_3       content_3       -               -           (nothing to do)
        content_3       content_8       -               -           (can remove unbreakable node)
        content_3       content_4       -               content_3
        content_3       content_5       -               #d          (can select the entire unbreakable node)
        content_5       content_8       content_6       content_6
        content_5       content_7       #e              #e          (select the entire unbreakable node)
        content_6       content_8       -               content_6
        content_7       content_8       -               content_8
        content_9       content_12      content_10      -
     *
     * @returns {WrappedRange}
     */
    _secureRange: function (options) {
        var self = this;
        var range = this.context.invoke('editor.createRange');
        var isCollapsed = range.isCollapsed();
        var needReselect = false;
        options = options || {};

        // move the start selection to an allowed node
        if (this.isUnbreakableNode(range.sc)) {
            var startPoint = dom[options.select === 'prev' ? 'prevPointUntil' : 'nextPointUntil']({node: range.sc, offset: range.so}, function (point) {
                return !self.isUnbreakableNode(point.node) && dom.isVisiblePoint(point);
            });
            if (startPoint && startPoint.node !== range.sc) {
                needReselect = true;
                range.sc = startPoint.node;
                range.so = startPoint.offset;
                if (isCollapsed) {
                    range.ec = range.sc;
                    range.eo = range.so;
                }
            }
        }

        if (!isCollapsed) { // mouse selection or key selection with shiftKey
            // find the allowed ancestor
            var ancestors = dom.listAncestor(range.sc, this.isUnbreakableNode.bind(this));
            var allowedAncestor = ancestors.slice(-2,-1)[0];
            var editable = ancestors.length ? _.last(ancestors).parentNode : this.context.layoutInfo.editable[0];
            if ($(editable).hasClass('note-editable')) {
                allowedAncestor = editable;
            }

            // move the end selection to an allowed node in the allowed ancestor
            var endPoint = dom[options.select === 'next' ? 'nextPointUntil' : 'prevPointUntil']({node: range.ec, offset: range.eo}, function (point) {
                return point.node === range.sc ||
                        !!dom.ancestor(point.node, function (node) { return node === allowedAncestor;}) &&
                        !self.isUnbreakableNode(point.node) && dom.isVisiblePoint(point);
            });
            if (endPoint && endPoint.node !== range.ec) {
                needReselect = true;
                range.ec = endPoint.node;
                range.eo = endPoint.offset;
            }
        }

        if (needReselect) {
            range = range.normalize().select();
            this.context.invoke('editor.saveRange');
        }
        return range;
    },

    //--------------------------------------------------------------------------
    // Handler
    //--------------------------------------------------------------------------

    _onRange: function () {
        var range = this._secureRange();
        this._focusNode(range.sc);
    },
    _onMouseUp: function () {
        var range = this._secureRange();
        this._focusNode(range.ec);
    },
    /*
     * prevents changes to unbreakable nodes
     *
     * @param {SummernoteEvent} se
     * @param {jQueryEvent} se
     */
    _onKeydown: function (se, e) {
        if (e.key.length !== 1 && e.keyCode !== 8 && e.keyCode !== 46) {
            return;
        }
        var self = this;
        // rerange to prevent some edition.
        // eg: if the user select with arraw and shifKey and keypress an other char
        var range = this._secureRange();
        var target = {node: range.sc, offset: range.so};

        if (e.key.length === 1) { // printable Char (eg: juste after a icon, we prevent to write into the icon)
            if (range.isCollapsed() && this.isUnbreakableNode(target.node)) {
                target = dom.nextPointUntil(dom.nextPoint(target), function (point) {
                    return dom.isText(point.node) && dom.isVisiblePoint(point);
                });
                if (!target) {
                    e.preventDefault();
                    return;
                }
                target.node.textContent = '§' + target.node.textContent;
                range.sc = range.ec = target.node;
                range.so = range.eo = 1;
                range = range.normalize().select();
                setTimeout(function () {
                    if (target.node.textContent[0] === '§') {
                        target.node.textContent = target.node.textContent.slice(1);
                        range = range.normalize().select();
                        self._focusNode(range.ec);
                    }
                });
            } else {
                setTimeout(function () {
                    self._focusNode(range.ec);
                });
            }
        } else if (e.keyCode === 8) { // backspace
            if (this.isUnbreakableNode(target.node)) {
                e.preventDefault();
            }
        } else if (e.keyCode === 46) { // delete
            target = dom.nextPointUntil(dom.nextPoint(target), dom.isVisiblePoint);
            if (this.isUnbreakableNode(target.node)) {
                e.preventDefault();
            }
        }
        if (e.keyCode === 8 || e.keyCode === 46) {
            var targetNode = target.node.tagName ? target.node : target.node.parentNode;
            if (dom.isMedia(targetNode)) {
                $(targetNode).remove();
                this.context.triggerEvent('change', this.$editable.html());
            }
            setTimeout(function () {
                self._focusNode(range.ec);
            });
        }
    },
    /*
     * prevents selection of unbreakable nodes
     *
     * @param {SummernoteEvent} se
     * @param {jQueryEvent} se
     */
    _onKeyup: function (se, e) {
        if (e.keyCode < 37 || e.keyCode > 40) {
            return;
        }
        var range;
        if (e.keyCode === 37) { // left
            range = this._secureRange({select: 'prev'});
            this._focusNode(range.sc);
        } else if (e.keyCode === 39) { // right
            range = this._secureRange({select: 'next'});
            this._focusNode(range.ec);
        } else if (e.keyCode === 38) { // up
            range = this._secureRange({select: 'prev'});
            this._focusNode(range.sc);
        } else { // down
            range = this._secureRange({select: 'next'});
            this._focusNode(range.ec);
        }
    },
});

registry.add('UnbreakablePlugin', Unbreakable);

return Unbreakable;

});
