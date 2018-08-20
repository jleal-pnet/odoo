odoo.define('web.nvd3.extensions', function () {
'use strict';

/**
 * The nvd3 library extensions and fixes should be done here to avoid patching
 * in place.
 */

nv.dev = false;  // sets nvd3 library in production mode

// monkey patch nvd3 to allow removing eventhandler on windowresize events
// see https://github.com/novus/nvd3/pull/396 for more details

// Adds a resize listener to the window.
nv.utils.onWindowResize = function (fun) {
    if (fun === null) return;
    window.addEventListener('resize', fun);
};

// Backwards compatibility with current API.
nv.utils.windowResize = nv.utils.onWindowResize;

// Removes a resize listener from the window.
nv.utils.offWindowResize = function (fun) {
    if (fun === null) return;
    window.removeEventListener('resize', fun);
};

// monkey patch nvd3 to prevent crashes when user changes view and nvd3
// tries to remove tooltips after 500 ms...  seriously nvd3, what were you
// thinking?
nv.tooltip.cleanup = function () {
    $('.nvtooltip').remove();
};

// monkey patch nvd3 to prevent it to display a tooltip (position: absolute)
// with a negative `top`; with this patch the highest tooltip's position is
// still in the graph
var originalCalcTooltipPosition = nv.tooltip.calcTooltipPosition;
nv.tooltip.calcTooltipPosition = function () {
    var container = originalCalcTooltipPosition.apply(this, arguments);
    container.style.top = container.style.top.split('px')[0] < 0 ? 0 + 'px' : container.style.top;
    return container;
};

// monkey patch nvd3 to translate "No Data Available"
var core = require('web.core');
var _t = core._t;
nv.utils.noData = function(chart, container) {
    var opt = chart.options(),
        margin = opt.margin(),
        noData = opt.noData(),
        data = (noData == null) ? [_t("No Data Available.")] : [noData],
        height = nv.utils.availableHeight(null, container, margin),
        width = nv.utils.availableWidth(null, container, margin),
        x = margin.left + width/2,
        y = margin.top + height/2;

    //Remove any previously created chart components
    container.selectAll('g').remove();

    var noDataText = container.selectAll('.nv-noData').data(data);

    noDataText.enter().append('text')
        .attr('class', 'nvd3 nv-noData')
        .attr('dy', '-.7em')
        .style('text-anchor', 'middle');

    noDataText
        .attr('x', x)
        .attr('y', y)
        .text(function(t){ return t; });
};

});
