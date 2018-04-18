odoo.define("account_invoice_import_xml.attachments", function (require) {
"use strict";

var relational_fields = require("web.relational_fields");
var FieldMany2ManyBinaryMultiFiles = relational_fields.FieldMany2ManyBinaryMultiFiles;
var field_registry = require("web.field_registry");
var field_utils = require('web.field_utils');
var session = require('web.session');

var core = require("web.core");
var qweb = core.qweb;

var ImportXMLAttachmentsWidget = FieldMany2ManyBinaryMultiFiles.extend({

    // @override
    init: function () {
        this._super.apply(this, arguments);
        this.xmlMetadata = {};
    },
    // @override
    _render: function(){
        this._generatedMetadata();
        this.$('.oe_placeholder_files, .oe_attachments')
            .replaceWith($(qweb.render('import_xmls_widget_files', {
                widget: this,
                show_table: Object.keys(this.value.data).length + Object.keys(this.uploadingFiles).length > 0,
            })));
        this.$('.oe_fileupload').show();
    },

    // @override
    _onFileLoaded: function(){
        var self = this;
        var files = Array.prototype.slice.call(arguments, 1);
        this.uploadingFiles = [];

        var attachment_ids = this.value.res_ids;
        _.each(files, function (file){
            if (file.error) {
                self.do_warn(_t('Uploading Error'), file.error);
            }else{
                attachment_ids.push(file.id);
                self.uploadedFiles[file.id] = true;
            }
        });

        this._rpc({
            model: 'account.invoice.xml.import',
            method: 'get_js_attachment_types',
            args: [attachment_ids],
        })
        .then(function(result){
            for(var key in result){
                if(result[key].type === null)
                    result[key].type = '';
                this.xmlMetadata[key] = result[key];
            };

            this._setValue({
                operation: 'REPLACE_WITH',
                ids: attachment_ids,
            });
        }.bind(this));
    },
});

field_registry.add("import_xmls", ImportXMLAttachmentsWidget);

});
