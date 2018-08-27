odoo.define('mail.AttachmentBox', function (require) {
"use strict";


var core = require('web.core');
var DocumentViewer = require('mail.DocumentViewer');
var QWeb = core.qweb;
var Widget = require('web.Widget');

var AttachmentBox = Widget.extend({
    events: {
    "click .o_attachment_download": "_onAttachmentDownload",
    "click .o_attachment_view": "_onAttachmentView",
    },
    /**
     * @override
     * @param {widget} parent
     * @param {Object} record
     */
    init: function (parent, record, options) {
        this._super.apply(this, arguments);
        this.current_res_id = record.res_id;
        this.current_res_model = record.model;
;
    },
    /**
     * @override
     */
    willStart: function () {
        var self = this;
        var domain = [
            ['res_id', '=', this.current_res_id],
            ['res_model', '=', this.current_res_model],
        ];
        var fields = ['name', 'url', 'type', 'mimetype', 'datas_fname'];
        return $.when(this._super.apply(this, arguments), this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: domain,
            fields: fields,
        }).then(function(result) {
                self.fullAttachments = result;
            }));
    },
    /**
     * @override
     */
    start: function () {
        var images = {};
        var others = {};
        if (this.fullAttachments) {
                var sortedAttachments = _.partition(this.fullAttachments, function (att) {
                    return att.mimetype && att.mimetype.split('/')[0] === 'image';
                });
                images = sortedAttachments[0];
                others = sortedAttachments[1];
            }

        this.$el.html(QWeb.render('mail.chatter.AttachmentBox', {
            imageList: images,
            otherList: others,
        }));
        this.$el.toggleClass('o_mail_chatter_attachments', true);
    },
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    /**
    * @param {Object} record
    */
    update: function (record) {
        this.current_res_id = record.res_id;
        this.current_res_model = record.model;
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onAttachmentDownload: function (ev) {
        ev.stopPropagation();
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onAttachmentView: function (ev) {
        ev.stopPropagation();
        var activeAttachmentID = $(ev.currentTarget).data('id');
        if (activeAttachmentID) {
            var attachmentViewer = new DocumentViewer(this, this.fullAttachments, activeAttachmentID);
            attachmentViewer.appendTo($('body'));
        }
    },

});

return AttachmentBox;
});

