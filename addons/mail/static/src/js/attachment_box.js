odoo.define('mail.AttachmentBox', function (require) {
"use strict";


    var Widget = require('web.Widget');
    var AbstractField = require('web.AbstractField');
    var DocumentViewer = require('mail.DocumentViewer');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

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

            options = options || {};
            this.local_res_id = record.res_id;
        },
        /**
         * @override
         */
        willStart: function () {
            var self = this;
            var domain = [
                ['res_id', '=', this.local_res_id],
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
        /**
        * @param {Object} record
        */
        update: function (record) {
            this.local_res_id = record.res_id;
        },

        /**
         * @private
         * @param {MouseEvent} event
         */
        _onAttachmentDownload: function (event) {
            event.stopPropagation();
        },
        /**
         * @private
         * @param {MouseEvent} event
         */
        _onAttachmentView: function (event) {
            event.stopPropagation();
            var activeAttachmentID = $(event.currentTarget).data('id');
            if (activeAttachmentID) {
                var attachmentViewer = new DocumentViewer(this, this.fullAttachments, activeAttachmentID);
                attachmentViewer.appendTo($('body'));
            }
        },

    });

    return AttachmentBox;
});

