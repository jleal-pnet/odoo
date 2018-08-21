odoo.define('web_editor.summernote.plugin.Font', function (require) {
'use strict';

var core = require('web.core');
var ColorpickerDialog = require('wysiwyg.widgets.ColorpickerDialog');
var AbstractPlugin = require('web_editor.summernote.plugin.abstract');
var registry = require('web_editor.summernote.plugin.registry');

var QWeb = core.qweb;
var _t = core._t;

var dom = $.summernote.dom;
var sOptions = $.summernote.options;
var sLang = $.summernote.lang.odoo;

//--------------------------------------------------------------------------
// helper for Font
//--------------------------------------------------------------------------

function isVisibleText (textNode) {
  return !!textNode.textContent.match(/\S|\u00A0/);
}
function orderClass (node) {
    var className = node.getAttribute && node.getAttribute('class');
    if (!className) return null;
    className = className.replace(/[\s\n\r]+/, ' ').replace(/^ | $/g, '').replace(/ +/g, ' ');
    if (!className.length) {
        node.removeAttribute("class");
        return null;
    }
    className = className.split(" ");
    className.sort();
    className = className.join(" ");
    node.setAttribute('class', className);
    return className;
}
function orderStyle (node) {
  var style = node.getAttribute('style');
  if (!style) return null;
  style = style.replace(/[\s\n\r]+/, ' ').replace(/^ ?;? ?| ?;? ?$/g, '').replace(/ ?; ?/g, ';');
  if (!style.length) {
      node.removeAttribute("style");
      return null;
  }
  style = style.split(";");
  style.sort();
  style = style.join("; ")+";";
  node.setAttribute('style', style);
  return style;
}
function getComputedStyle (node) {
    return node.nodeType === Node.COMMENT_NODE ? {} : window.getComputedStyle(node);
}
function moveContent (from, to) {
  if (from === to) {
    return;
  }
  if (from.parentNode === to) {
    while (from.lastChild) {
      dom.insertAfter(from.lastChild, from);
    }
  } else {
    while (from.firstChild && from.firstChild !== to) {
      to.appendChild(from.firstChild);
    }
  }
}

//--------------------------------------------------------------------------
// Font (colorpicker & font-size)
//--------------------------------------------------------------------------

dom.isFont = function (node) {
    return node && node.tagName === "FONT" || dom.isIcon(node);
};

var Font = AbstractPlugin.extend({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    colorPickerButton: function ($button) {
        if (!QWeb.has_template('web_editor.colorpicker')) {
            return $button;
        }

        var self = this;
        var $palettes = $button.find('.note-palette');
        var $bgPalette = $palettes.first();
        var $forePalette = $palettes.last();

        // fore palette

        $forePalette = this._createPalette($forePalette);
        $forePalette.find("button:not(.note-color-btn)")
            .addClass("note-color-btn")
            .attr('data-event', 'foreColor')
            .each(function () {
                var $el = $(this);
                var className = $el.hasClass('o_custom_color') ? $el.data('color') : 'text-' + $el.data('color');
                $el.attr('data-value', className).addClass($el.hasClass('o_custom_color') ? '' : 'bg-' + $el.data('color'));
            });
        var $foreCustomColor = $('<h6 class="note-custom-color mt8" data-event="customColor" data-value="foreColor"/>').text(this.lang.color.customColor);
        $forePalette.append($foreCustomColor);

        // bg palette

        $bgPalette = this._createPalette($bgPalette);
        var $bg = $bgPalette.find("button:not(.note-color-btn)")
            .addClass("note-color-btn")
            .attr('data-event', 'backColor')
            .each(function () {
                var $el = $(this);
                var className = $el.hasClass('o_custom_color') ? $el.data('color') : 'bg-' + $el.data('color');
                $el.attr('data-value', className).addClass($el.hasClass('o_custom_color') ? '' : className);
            });
        var $bgCustomColor = $('<h6 class="note-custom-color mt8" data-event="customColor" data-value="backColor"/>').text(this.lang.color.customColor);
        $bgPalette.append($bgCustomColor);

        // split 2 buttons

        $button.find('.note-current, .note-palette-title, .note-current-color-button').remove();
        $button.find('.dropdown-toggle').html('<i class="' + this.options.icons.font + '">');
        $button.removeClass('note-color');

        $bgPalette.detach();
        var $bgContainer = $button.clone();
        $bgContainer.find('.dropdown-toggle').html('<i class="' + this.options.icons.bg + '">');
        $bgContainer.find('.note-palette').replaceWith($bgPalette);

        $button.addClass('note-fore-color');
        $bgContainer.addClass('note-bg-color');

        $button = $button.add($bgContainer);

        // add event

        $button.on('mousedown', function (ev) {
            self.context.invoke('editor.saveRange');
        });
        $button.find('[data-event="foreColor"]').on('click', this._wrapCommand(this.context.createInvokeHandlerAndUpdateState('Font.changeForeColor')));
        $button.find('[data-event="backColor"]').on('click', this._wrapCommand(this.context.createInvokeHandlerAndUpdateState('Font.changeBgColor')));
        $foreCustomColor.add($bgCustomColor).on('mousedown', this._onCustomColor.bind(this));

        $button.find('[data-event]').removeAttr('data-event');

        return $button;
    },

    fontSizeButton: function ($button) {
        $button.find('.dropdown-menu').off('click').on('click', this.context.createInvokeHandlerAndUpdateState('Font.changeFontSize'));
        return $button;
    },

    changeForeColor: function (color) {
        this._applyFont(color, null, null);
    },
    changeBgColor: function (color) {
        this._applyFont(null, color, null);
    },
    changeFontSize: function (fontsize) {
        this._applyFont(null, null, fontsize);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _applyFont: function (color, bgcolor, size) {
        var r = this.context.invoke('editor.createRange');
        if (!r) {
            return;
        }
        if (r.isCollapsed() && !dom.isIcon(r.sc)) {
            var target = this.context.invoke('editor.restoreTarget');
            if (target) {
                r.sc = r.ec = target;
                r.so = r.eo = 0;
            }
        }

        var startPoint = r.getStartPoint();
        var endPoint = r.getEndPoint();
        if (r.isCollapsed() && !dom.isIcon(r.sc)) {
            return {
                sc: startPoint.node,
                so: startPoint.offset,
                ec: endPoint.node,
                offset: endPoint.offset
            };
        }
        if (startPoint.node.tagName && startPoint.node.childNodes[startPoint.offset]) {
            startPoint.node = startPoint.node.childNodes[startPoint.offset];
            startPoint.offset = 0;
        }
        if (endPoint.node.tagName && endPoint.node.childNodes[endPoint.offset]) {
            endPoint.node = endPoint.node.childNodes[endPoint.offset];
            endPoint.offset = 0;
        }
        // get first and last point
        var ancestor;
        var node;
        if (endPoint.offset && endPoint.offset !== dom.nodeLength(endPoint.node)) {
            ancestor = dom.ancestor(endPoint.node, dom.isFont) || endPoint.node;
            dom.splitTree(ancestor, endPoint);
        }
        if (startPoint.offset && startPoint.offset !== dom.nodeLength(startPoint.node)) {
            ancestor = dom.ancestor(startPoint.node, dom.isFont) || startPoint.node;
            node = dom.splitTree(ancestor, startPoint);
            if (endPoint.node === startPoint.node) {
                endPoint.node = node;
                endPoint.offset = dom.nodeLength(node);
            }
            startPoint.node = node;
            startPoint.offset = 0;
        }
        // get list of nodes to change
        var nodes = [];
        dom.walkPoint(startPoint, endPoint, function (point) {
            var node = point.node;
            if (((dom.isText(node) && isVisibleText(node)) || dom.isIcon(node)) &&
            (node !== endPoint.node || endPoint.offset)) {
                nodes.push(point.node);
            }
        });
        nodes = _.unique(nodes);
        // If ico fa
        if (r.isCollapsed()) {
            nodes.push(startPoint.node);
        }
        // apply font: foreColor, backColor, size (the color can be use a class text-... or bg-...)
        var font, $font, fonts = [], style, className;
        var i;
        if (color || bgcolor || size) {
            for (i=0; i<nodes.length; i++) {
                node = nodes[i];
                font = dom.ancestor(node, dom.isFont);
                if (!font) {
                    if (node.textContent.match(/^[ ]|[ ]$/)) {
                        node.textContent = node.textContent.replace(/^[ ]|[ ]$/g, '\u00A0');
                    }
                    font = dom.create("font");
                    node.parentNode.insertBefore(font, node);
                    font.appendChild(node);
                }
                fonts.push(font);
                className = font.className.split(/\s+/);
                var k;
                if (color) {
                    for (k=0; k<className.length; k++) {
                        if (className[k].length && className[k].slice(0,5) === "text-") {
                            className.splice(k,1);
                            k--;
                        }
                    }
                    if (color === 'text-undefined') {
                        font.className = className.join(" ");
                        font.style.color = "inherit";
                    } else if (color.indexOf('text-') !== -1) {
                        font.className = className.join(" ") + " " + color;
                        font.style.color = "inherit";
                    } else {
                        font.className = className.join(" ");
                        font.style.color = color;
                    }
                }
                if (bgcolor) {
                    for (k=0; k<className.length; k++) {
                        if (className[k].length && className[k].slice(0,3) === "bg-") {
                            className.splice(k,1);
                            k--;
                        }
                    }

                    if (bgcolor === 'bg-undefined') {
                        font.className = className.join(" ");
                        font.style.backgroundColor = "inherit";
                    } else if (bgcolor.indexOf('bg-') !== -1) {
                        font.className = className.join(" ") + " " + bgcolor;
                        font.style.backgroundColor = "inherit";
                    } else {
                        font.className = className.join(" ");
                        font.style.backgroundColor = bgcolor;
                    }
                }
                if (size) {
                    font.style.fontSize = "inherit";
                    if (!isNaN(size) && Math.abs(parseInt(getComputedStyle(font).fontSize, 10)-size)/size > 0.05) {
                        font.style.fontSize = size + "px";
                    }
                }
            }
        }
        // remove empty values
        // we must remove the value in 2 steps (applay inherit then remove) because some
        // browser like chrome have some time an error for the rendering and/or keep inherit
        for (i=0; i<fonts.length; i++) {
            font = fonts[i];
            if (font.style.color === "inherit") {
                font.style.color = "";
            }
            if (font.style.backgroundColor === "inherit") {
                font.style.backgroundColor = "";
            }
            if (font.style.fontSize === "inherit") {
                font.style.fontSize = "";
            }
            $font = $(font);
            if (font.style.color === '' && font.style.backgroundColor === '' && font.style.fontSize === '') {
                $font.removeAttr("style");
            }
            if (!font.className.length) {
                $font.removeAttr("class");
            }
        }
        // select nodes to clean (to remove empty font and merge same nodes)
        nodes = [];
        dom.walkPoint(startPoint, endPoint, function (point) {
            nodes.push(point.node);
        });
        nodes = _.unique(nodes);
        function remove(node, to) {
            if (node === endPoint.node) {
                endPoint = dom.prevPoint(endPoint);
            }
            if (to) {
                moveContent(node, to);
            }
            dom.remove(node);
        }
        // remove node without attributes (move content), and merge the same nodes
        for (i=0; i<nodes.length; i++) {
            node = nodes[i];
            if ((dom.isText(node) || dom.isBR(node)) && !isVisibleText(node)) {
                remove(node);
                nodes.splice(i,1);
                i--;
                continue;
            }
            font = dom.ancestor(node, dom.isFont);
            node = font || dom.ancestor(node, dom.isSpan);
            if (!node) {
                continue;
            }
            $font = $(node);
            className = orderClass(node);
            style = orderStyle(node);
            if (!className && !style) {
                remove(node, node.parentNode);
                nodes.splice(i,1);
                i--;
                continue;
            }
            if (i>0 && (font = dom.ancestor(nodes[i-1], dom.isFont))) {
                if (font === node.previousElementSibling) {
                    if (font === node.previousElementSibling &&
                        node !== font && className === font.getAttribute('class') && style === font.getAttribute('style')) {
                        remove(node, font);
                        nodes.splice(i,1);
                        i--;
                        continue;
                    }
                }
            }
        }

        // restore selection
        r.sc = startPoint.node;
        r.so = startPoint.offset;
        r.ec = endPoint.node;
        r.eo = endPoint.offset;
        r.normalize().select();
    },

    _createPalette: function ($palette, options) {
        var $clpicker = $(QWeb.render('web_editor.colorpicker'));
        var groups;

        if ($clpicker.is("colorpicker")) {
            groups = _.map($clpicker.find('[data-name="theme"], [data-name="transparent_grayscale"]'), function (el) {
                return $(el).find("button").empty();
            });
        } else {
            groups = [$clpicker.find("button").empty()];
        }

        var html = "<h6 class='mt-2'>" + _t("Theme colors") + "</h6>" + _.map(groups, function ($group) {
            if (!$group.length) {
                return '';
            }
            var $row = $("<div/>", {"class": "note-color-row mb8"}).append($group);
            var $after_breaks = $row.find(".o_small + :not(.o_small)");
            if ($after_breaks.length === 0) {
                $after_breaks = $row.find(":nth-child(8n+9)");
            }
            $after_breaks.addClass("o_clear");
            return $row[0].outerHTML;
        }).join("") + "<h6 class='mt-2'>" + _t("Common colors") + "</h6>";

        $palette.find('.note-color-palette').prepend(html);
         // Find the custom colors which are used in the page and add them to the color palette
        var colors = [];
        var $editable = window.__EditorMenuBar_$editable || $();
        _.each($editable.find('[style*="color"]'), function (element) {
            if (element.style.color) {
                colors.push(element.style.color);
            }
            if (element.style.backgroundColor) {
                colors.push(element.style.backgroundColor);
            }
        });
        return $palette;
    },

    _rgbToHex: function(rgb) {
        var rgbSplit = rgb.match(/rgb\((\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)/);
        if (!rgbSplit) {
            return rgbSplit;
        }
        var hex = ColorpickerDialog.prototype.convertRgbToHex(
            parseInt(rgbSplit[1]),
            parseInt(rgbSplit[2]),
            parseInt(rgbSplit[3])
        );
        if (!hex) {
            throw new Error('Wrong Color');
        }
        return hex.hex.toUpperCase();
    },

    _onCustomColor: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();

        var self = this;
        var targetColor = $(ev.target).data('value');
        var target = this.context.invoke('editor.restoreTarget');
        var colorPickerDialog = new ColorpickerDialog(this.options.parent, this.options.recordInfo());
        colorPickerDialog.on('colorpicker:saved', this, this._wrapCommand(function (ev) {
            self.context.invoke('editor.saveTarget', target);
            if (targetColor === 'foreColor') {
                self._applyFont(ev.data.hex, null, null);
            } else {
                self._applyFont(null, ev.data.hex, null);
            }
        }));
        colorPickerDialog.open();
        this.context.invoke('MediaPlugin.hidePopovers');
    },
});

_.extend(sOptions.icons, {
    font: 'fa fa-font',
    bg: 'fa fa-paint-brush',
});
_.extend(sLang.color, {
    customColor: _t('Custom Color'),
});

registry.add('Font', Font);

return Font;

});
