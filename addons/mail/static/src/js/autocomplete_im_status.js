odoo.define('mail.autocomplete_im_status', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;

    /**
     * used when sending direct messages to a user
     * it will append the "im_status" icon (e.g "offline", "online", "...")
    */

    return {
        register_autocomplete_im_status: function(){
            $.widget('odoo.autocomplete_im_status', $.ui.autocomplete, {
                _renderItem: function(ul, item) {
                    var status = QWeb.render('mail.UserStatus', { status: item.im_status });
                    var $span = $('<span>').text(item.label).prepend(status);
                    var $a = $('<a>').append($span);
                    var $li = $('<li>').append($a);
                    return $li.appendTo(ul);
                }
            });
        }
    }
});