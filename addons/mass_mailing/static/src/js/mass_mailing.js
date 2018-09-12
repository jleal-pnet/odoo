odoo.define('mass_mailing.mass_mailing', function (require) {
"use strict";

var fieldRegistry = require('web.field_registry');
var KanbanRecord = require('web.KanbanRecord');
var KanbanColumn = require('web.KanbanColumn');
var convertInline = require('web_editor.convertInline');
var FieldHtml = require('web_editor.field.html');


KanbanRecord.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _openRecord: function () {
        if (this.modelName === 'mail.mass_mailing.campaign') {
            this.$('.oe_mailings').click();
        } else if (this.modelName === 'mail.mass_mailing.list' &&
                   this.$('.o_mailing_list_kanban_boxes a')) {
            this.$('.o_mailing_list_kanban_boxes a').first().click();
        } else {
            this._super.apply(this, arguments);
        }
    },
});

KanbanColumn.include({
    init: function () {
        this._super.apply(this, arguments);
        if (this.modelName === 'mail.mass_mailing') {
            this.draggable = false;
        }
    },
});


var MassmailingFieldHtml = FieldHtml.extend({
    /**
     * Commit the change in 'style-inline' on an other field
     * nodeOptions:
     *      - inline-field: fieldName to save the html value converted into inline code
     *
     * @override
     */
    commitChanges: function () {
        var fieldName = this.nodeOptions['inline-field'];

        return this.wysiwyg.save().then(function (isDirty) {
            this._isDirty = isDirty;

            var $editable = this.wysiwyg.getEditable();
            convertInline.attachmentThumbnailToLinkImg($editable);
            convertInline.fontToImg($editable);
            convertInline.classToStyle($editable);

            this.trigger_up('field_changed', {
                dataPointID: this.dataPointID,
                changes: _.object([fieldName], [$editable.html()])
            });

            if (this._isDirty && this.mode === 'edit') {
                return this._doAction();
            }
        }.bind(this));
    },

});


fieldRegistry.add('mass_mailing_html', MassmailingFieldHtml);

});
